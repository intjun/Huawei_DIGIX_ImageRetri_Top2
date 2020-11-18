'''
Author: your name
Date: 2020-08-16 23:05:53
LastEditTime: 2020-08-17 06:48:08
LastEditors: Please set LastEditors
Description: In User Settings Edit
FilePath: /PyRetri-master-gai1/pyretri/index/re_ranker/re_ranker_impl/fast_qe_kr_query.py
'''
'''
Author: your name
Date: 2020-08-16 23:05:53
LastEditTime: 2020-08-16 23:14:40
LastEditors: Please set LastEditors
Description: In User Settings Edit
FilePath: /PyRetri-master-gai1/pyretri/index/re_ranker/re_ranker_impl/qe_fast_kr_query.py
'''
# -*- coding: utf-8 -*-

import torch

from ...metric import MetricBase
from .query_expansion import QE
from .fast_k_reciprocal import Fast_KReciprocal
from ..re_ranker_base import ReRankerBase
from ...registry import RERANKERS

from typing import Dict

@RERANKERS.register
class fast_QEKR_query(ReRankerBase):
    """
    Apply query expansion and k-reciprocal.

    Hyper-Params:
        qe_times (int): number of query expansion times.
        qe_k (int): number of the neighbors to be combined.
        k1 (int): hyper-parameter for calculating jaccard distance.
        k2 (int): hyper-parameter for calculating local query expansion.
        lambda_value (float): hyper-parameter for calculating the final distance.
    """
    default_hyper_params = {
        "qe_times": 1,
        "qe_k": 1,
        "k1": 20,
        "k2": 6,
        "lambda_value": 0.3,
        "N":6000,
        "dist_type":"euclidean_distance"
    }

    def __init__(self, hps: Dict or None = None):
        """
        Args:
            hps (dict): default hyper parameters in a dict (keys, values).
        """
        super(fast_QEKR_query, self).__init__(hps)
        qe_hyper_params = {
            "qe_times": self._hyper_params["qe_times"],
            "qe_k": self._hyper_params["qe_k"],
        }
        kr_hyper_params = {
            "k1":self._hyper_params["k1"],
            "k2" : self._hyper_params["k2"],
            "lambda_value" : self._hyper_params["lambda_value"],
            "dist_type" : self._hyper_params["dist_type"],
            "N" : self._hyper_params["N"]
        }
        self.qe = QE(hps=qe_hyper_params)
        self.kr = Fast_KReciprocal(hps=kr_hyper_params)

    # def __call__(self, query_fea: torch.tensor, gallery_fea: torch.tensor, dis: torch.tensor or None = None,
    def __call__(self, query_fea: torch.tensor, gallery_fea: torch.tensor,metric:MetricBase, dis: torch.tensor or None = None,
                 sorted_index: torch.tensor or None = None) -> torch.tensor:

        # sorted_index = self.qe(query_fea, gallery_fea, dis, kr=self.kr)
        # jerry
        query_fea_tmp=query_fea.detach()
        dis=metric._cal_dis(query_fea, query_fea_tmp)
        sorted_index = torch.argsort(dis, dim=1)
        for i in range(self._hyper_params['qe_times']):
            sorted_index = sorted_index[:, :self._hyper_params['qe_k']]
            sorted_index = sorted_index.reshape(-1)
            requery_fea = query_fea_tmp[sorted_index].view(query_fea.shape[0], -1, query_fea.shape[1]).sum(dim=1)
            requery_fea = requery_fea + query_fea
            
            # query_fea = requery_fea
            #   jerry
            query_fea = requery_fea/(self._hyper_params['qe_k']+1)
            
        sorted_index = self.kr(query_fea, gallery_fea,metric)

        return sorted_index

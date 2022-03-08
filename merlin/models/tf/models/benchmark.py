#
# Copyright (c) 2021, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from typing import List, Optional, Union

from merlin.schema import Schema

from ..blocks.core.aggregation import ElementWiseMultiply
from ..blocks.mlp import MLPBlock
from ..blocks.retrieval.matrix_factorization import MatrixFactorizationBlock
from ..core import Model, ParallelBlock, ParallelPredictionBlock, PredictionTask
from .utils import parse_prediction_tasks


def NCFModel(
    schema: Schema,
    embedding_dim: int,
    mlp_block: MLPBlock,
    prediction_tasks: Optional[
        Union[PredictionTask, List[PredictionTask], ParallelPredictionBlock]
    ] = None,
    **kwargs
) -> Model:
    """NCF-model architecture.

    Example Usage::
        ncf = NCFModel(schema, embedding_dim=64, mlp_block=MLPBlock([256, 64]))
        ncf.compile(optimizer="adam")
        ncf.fit(train_data, epochs=10)

    References
    ----------
    [1] Xiangnan, He, et al. "Neural Collaborative Filtering." arXiv:1708.05031 (2017).

    Parameters
    ----------
    schema : Schema
        The `Schema` with the input features
    embedding_dim : int
        Dimension of the embeddings
    mlp_block : MLPBlock
        Stack of MLP layers to learn  non-linear interactions.
    prediction_tasks: optional
        The prediction tasks to be used, by default this will be inferred from the Schema.

    Returns
    -------
    Model

    """

    mlp_branch = MatrixFactorizationBlock(schema, dim=embedding_dim).connect(mlp_block)
    mf_branch = MatrixFactorizationBlock(
        schema, dim=embedding_dim, aggregation=ElementWiseMultiply()
    )
    ncf = ParallelBlock({"mf": mf_branch, "mlp": mlp_branch}, aggregation="concat")

    prediction_tasks = parse_prediction_tasks(schema, prediction_tasks)
    model = ncf.connect(prediction_tasks)

    return model

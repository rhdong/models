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
import logging
from typing import Any, Callable, Dict, Optional, Union

from merlin.models.tf.blocks.core.aggregation import ElementWiseMultiply
from merlin.models.tf.blocks.core.transformations import RenameFeatures
from merlin.models.tf.blocks.retrieval.base import DualEncoderBlock
from merlin.models.tf.features.embedding import EmbeddingFeatures, EmbeddingOptions
from merlin.schema import Schema, Tags

LOG = logging.getLogger("merlin_models")


class QueryItemIdsEmbeddingsBlock(DualEncoderBlock):
    def __init__(
        self,
        schema: Schema,
        dim: int,
        query_id_tag=Tags.USER_ID,
        item_id_tag=Tags.ITEM_ID,
        embeddings_initializers: Optional[Dict[str, Callable[[Any], None]]] = None,
        **kwargs,
    ):
        query_schema = schema.select_by_tag(query_id_tag)
        item_schema = schema.select_by_tag(item_id_tag)
        embedding_options = EmbeddingOptions(
            embedding_dim_default=dim, embeddings_initializers=embeddings_initializers
        )

        rename_features = RenameFeatures(
            {query_id_tag: "query", item_id_tag: "item"}, schema=schema
        )
        post = kwargs.pop("post", None)
        if post:
            post = rename_features.connect(post)
        else:
            post = rename_features

        embedding = lambda s: EmbeddingFeatures.from_schema(  # noqa
            s, embedding_options=embedding_options
        )

        super().__init__(  # type: ignore
            embedding(query_schema), embedding(item_schema), post=post, **kwargs
        )

    def export_embedding_table(self, table_name: Union[str, Tags], export_path: str, gpu=True):
        if table_name in ("item", Tags.ITEM_ID):
            return self.item_block().block.export_embedding_table(table_name, export_path, gpu=gpu)

        return self.query_block().block.export_embedding_table(table_name, export_path, gpu=gpu)

    def embedding_table_df(self, table_name: Union[str, Tags], gpu=True):
        if table_name in ("item", Tags.ITEM_ID):
            return self.item_block().block.embedding_table_df(table_name, gpu=gpu)

        return self.query_block().block.embedding_table_df(table_name, gpu=gpu)


def MatrixFactorizationBlock(
    schema: Schema,
    dim: int,
    query_id_tag=Tags.USER_ID,
    item_id_tag=Tags.ITEM_ID,
    embeddings_initializers: Optional[Dict[str, Callable[[Any], None]]] = None,
    aggregation=ElementWiseMultiply(),
    **kwargs,
):
    return QueryItemIdsEmbeddingsBlock(
        schema=schema,
        dim=dim,
        query_id_tag=query_id_tag,
        item_id_tag=item_id_tag,
        embeddings_initializers=embeddings_initializers,
        aggregation=aggregation,
        **kwargs,
    )

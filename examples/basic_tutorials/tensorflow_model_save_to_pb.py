#! /usr/bin/python
# -*- coding: utf-8 -*-

# When TensorFlow is the backend, save the model in .pb format.
# Reference: https://leimao.github.io/blog/Save-Load-Inference-From-TF2-Frozen-Graph/

import os
os.environ['TL_BACKEND'] = 'tensorflow'

import numpy as np
import tensorflow as tf
import tensorlayerx as tlx
from tensorlayerx.nn import Module
from tensorlayerx.nn import Linear, Dropout, BatchNorm1d
from tensorflow.python.framework.convert_to_constants import convert_variables_to_constants_v2


class CustomModel(Module):

    def __init__(self):
        super(CustomModel, self).__init__()
        self.dropout1 = Dropout(p=0.2)
        self.linear1 = Linear(out_features=800, in_features=784)
        self.batchnorm = BatchNorm1d(act=tlx.nn.ReLU, num_features=800)
        self.dropout2 = Dropout(p=0.2)
        self.linear2 = Linear(out_features=800, act=tlx.nn.ReLU, in_features=800)
        self.dropout3 = Dropout(p=0.2)
        self.linear3 = Linear(out_features=10, act=tlx.nn.ReLU, in_features=800)

    def forward(self, x):
        z = self.dropout1(x)
        z = self.linear1(z)
        z = self.batchnorm(z)
        z = self.dropout2(z)
        z = self.linear2(z)
        z = self.dropout3(z)
        out = self.linear3(z)
        return out

    # # forward can also be defined this way
    # def forward(self, x):
    #     z = self.dropout1.forward(x)
    #     z = self.linear1.forward(z)
    #     z = self.batchnorm.forward(z)
    #     z = self.dropout2.forward(z)
    #     z = self.linear2.forward(z)
    #     z = self.dropout3.forward(z)
    #     out = self.linear3.forward(z)
    #     return out

    @tf.function(experimental_relax_shapes=True)
    def infer(self, x):
        return self.forward(x)


net = CustomModel()
net.set_eval()

# frozen graph
input_signature = tf.TensorSpec([None, 784])
concrete_function = net.infer.get_concrete_function(x=input_signature)
frozen_graph = convert_variables_to_constants_v2(concrete_function)
frozen_graph_def = frozen_graph.graph.as_graph_def()
tf.io.write_graph(graph_or_graph_def=frozen_graph_def, logdir="./", name=f"mlp.pb", as_text=False)

# Because frozen graph has been sort of being deprecated by TensorFlow, and SavedModel format is encouraged to use,
# we would have to use the TensorFlow 1.x function to load the frozen graph from hard drive.

with tf.io.gfile.GFile("mlp.pb", "rb") as f:
    graph_def = tf.compat.v1.GraphDef()
    loaded = graph_def.ParseFromString(f.read())

with tf.Graph().as_default() as graph:
    tf.compat.v1.import_graph_def(graph_def, name="")

x = graph.get_tensor_by_name("x:0")
y = graph.get_tensor_by_name("Identity:0")

bathc_image = np.ones([1, 784])
with tf.compat.v1.Session(graph=graph) as sess:
    feed_dict_testing = {x: bathc_image}
    out = sess.run(y, feed_dict=feed_dict_testing)
    print(out)

# Copyright 2021 The TensorFlow Authors. All Rights Reserved.
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
# ==============================================================================
"""Tests for analyzer package."""

import tensorflow as tf

from tensorflow.lite.python import analyzer
from tensorflow.python.framework import test_util
from tensorflow.python.platform import resource_loader
from tensorflow.python.platform import test


class ConvertTest(test_util.TensorFlowTestCase):

  def testTxt(self):
    model_path = resource_loader.get_path_to_datafile('../testdata/add.bin')
    txt = analyzer.ModelAnalyzer.analyze(
        model_path=model_path, result_format='txt')
    self.assertIn('Subgraph#0(T#1) -> [T#2]', txt)
    self.assertIn('Op#0 ADD(T#1, T#1) -> [T#0]', txt)
    self.assertIn('Op#1 ADD(T#0, T#1) -> [T#2]', txt)

  def testHtml(self):
    model_path = resource_loader.get_path_to_datafile('../testdata/add.bin')
    html = analyzer.ModelAnalyzer.analyze(
        model_path=model_path, result_format='html')
    self.assertIn('<html>\n<head>', html)
    self.assertIn('ADD (0)', html)

  def testMlir(self):
    model_path = resource_loader.get_path_to_datafile('../testdata/add.bin')
    mlir = analyzer.ModelAnalyzer.analyze(
        model_path=model_path, result_format='mlir')
    self.assertIn(
        'func @main(%arg0: tensor<1x8x8x3xf32>) -> '
        'tensor<1x8x8x3xf32> attributes '
        '{tf.entry_function = {inputs = "input", outputs = "output"}}', mlir)
    self.assertIn(
        '%0 = tfl.add %arg0, %arg0 {fused_activation_function = "NONE"} : '
        'tensor<1x8x8x3xf32>', mlir)
    self.assertIn(
        '%1 = tfl.add %0, %arg0 {fused_activation_function = "NONE"} : '
        'tensor<1x8x8x3xf32>', mlir)
    self.assertIn('return %1 : tensor<1x8x8x3xf32>', mlir)

  def testMlirHugeConst(self):
    model_path = resource_loader.get_path_to_datafile(
        '../testdata/conv_huge_im2col.bin')
    mlir = analyzer.ModelAnalyzer.analyze(
        model_path=model_path, result_format='mlir')
    self.assertIn(
        '%1 = "tfl.pseudo_const"() {value = opaque<"_", "0xDEADBEEF"> : '
        'tensor<3x3x3x8xf32>} : () -> tensor<3x3x3x8xf32>', mlir)

  def testTxtWithFlatBufferModel(self):

    @tf.function(
        input_signature=[tf.TensorSpec(shape=[None], dtype=tf.float32)])
    def func(x):
      return x + tf.cos(x)

    converter = tf.lite.TFLiteConverter.from_concrete_functions(
        [func.get_concrete_function()])
    fb_model = converter.convert()
    txt = analyzer.ModelAnalyzer.analyze(
        model_content=fb_model, result_format='txt')
    self.assertIn('Subgraph#0 main(T#0) -> [T#2]', txt)
    self.assertIn('Op#0 COS(T#0) -> [T#1]', txt)
    self.assertIn('Op#1 ADD(T#0, T#1) -> [T#2]', txt)

  def testMlirWithFlatBufferModel(self):

    @tf.function(
        input_signature=[tf.TensorSpec(shape=[None], dtype=tf.float32)])
    def func(x):
      return x + tf.cos(x)

    converter = tf.lite.TFLiteConverter.from_concrete_functions(
        [func.get_concrete_function()])
    fb_model = converter.convert()
    mlir = analyzer.ModelAnalyzer.analyze(
        model_content=fb_model, result_format='mlir')
    self.assertIn('func @main(%arg0: tensor<?xf32>) -> tensor<?xf32>', mlir)
    self.assertIn('%0 = "tfl.cos"(%arg0) : (tensor<?xf32>) -> tensor<?xf32>',
                  mlir)
    self.assertIn(
        '%1 = tfl.add %arg0, %0 {fused_activation_function = "NONE"} : '
        'tensor<?xf32>', mlir)
    self.assertIn('return %1 : tensor<?xf32', mlir)

  def testHtmlWithFlatBufferModel(self):

    @tf.function(
        input_signature=[tf.TensorSpec(shape=[None], dtype=tf.float32)])
    def func(x):
      return x + tf.cos(x)

    converter = tf.lite.TFLiteConverter.from_concrete_functions(
        [func.get_concrete_function()])
    fb_model = converter.convert()
    html = analyzer.ModelAnalyzer.analyze(
        model_content=fb_model, result_format='html')
    self.assertIn('<html>\n<head>', html)
    self.assertIn('COS (0)', html)
    self.assertIn('ADD (1)', html)


if __name__ == '__main__':
  test.main()

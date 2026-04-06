import rclpy
from rclpy.node import Node
from autopartol_interfaces.srv import Speech
import espeakng

class Speaker(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        # 创建服务端，服务类型为Speech，服务名称为'speech'，回调函数为self.speak_callback
        self.speech_service = self.create_service(
            Speech, 'speech', self.speak_callback)
        # 创建espeakng对象，设置语音为中文
        self.speaker = espeakng.Speaker()
        self.speaker.voice = 'zh'
        # 日志提示服务端已启动
        self.get_logger().info('服务端已启动，等待客户端请求')  

    # 服务回调函数，用于处理客户端请求
    def speak_callback(self, request, response):
        self.get_logger().info('正在朗读 %s' % request.text)
        self.speaker.say(request.text)# 朗读请求中的文本
        self.speaker.wait()
        response.result = True
        return response


def main(args=None):
    rclpy.init(args=args)
    node = Speaker('speaker')# 创建节点，节点名称为'speaker'
    rclpy.spin(node)
    rclpy.shutdown()
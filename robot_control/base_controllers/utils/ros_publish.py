import random
import rospy as ros
from sensor_msgs.msg import JointState

from visualization_msgs.msg import Marker
from visualization_msgs.msg import MarkerArray

from geometry_msgs.msg import Point
import numpy as np

import roslaunch
import os
import rospkg

class RosPub():
    def __init__(self, robot_name="solo", only_visual = False, visual_frame = "world", node_name="sub_pub_node_python",topic="/joint_states",launch_rviz=True):

        print("Starting ros pub---------------------------------------------------------------")
        if (not only_visual):                           
            #launch rviz node if not yet done will start roscore too
            uuid = roslaunch.rlutil.get_or_generate_uuid(None, False)
            roslaunch.configure_logging(uuid)
            package = rospkg.RosPack().get_path('ros_impedance_controller') + '/launch/visualize.launch'
            cli_args = [package, 'robot_name:='+robot_name, 'test_joints:=false']
            roslaunch_args = cli_args[1:]
            roslaunch_file = [(roslaunch.rlutil.resolve_launch_arguments(cli_args)[0], roslaunch_args)]
            if(launch_rviz):
                parent = roslaunch.parent.ROSLaunchParent(uuid, roslaunch_file)
                parent.start()
                ros.loginfo("RVIZ started")

            # set joint state publisher
            self.joint_pub = ros.Publisher(topic, JointState, queue_size=1)

        #init ros node to publish joint states and vis topics
        node_name = node_name + str(int(random.random()*10000))
        ros.init_node(node_name, anonymous=False, log_level=ros.FATAL)

        self.marker_pub = ros.Publisher('/vis' , MarkerArray, queue_size=1)
        self.arrow_pub = ros.Publisher('/arrow', MarkerArray, queue_size=1)
        self.markerArray = MarkerArray()
        self.markerArray.markers = []
        self.markerArray_arrows = MarkerArray()
        self.markerArray_arrows.markers = []
        self.id = 0
        self.id_arrow = 0

        self.fixedBaseRobot = False
        self.visual_frame = visual_frame
        print("Initialized ros pub---------------------------------------------------------------")

    def publish(self,robot, q, qd = None, tau = None):
    
        if (qd is None ):
           qd = np.zeros(robot.nv)
        if (tau is None ):
           tau = np.zeros(robot.nv)
                                
        all_names = [name for name in robot.model.names]            
        msg = JointState()
        msg.header.stamp = ros.Time.now() 
        # check if it is a floating base robot
        try:
            if(robot.nq != robot.nv):
                self.fixedBaseRobot = False
        except:
            self.fixedBaseRobot = True
            
        msg.name = all_names[-robot.na:] #remove universe joint that is not active
        msg.position = q                
        msg.velocity = qd                
        msg.effort = tau
        """
        print("message to publish(ros_publisher):")
        print(msg)
        print("fine messaggio---------------------------")
        """
        self.joint_pub.publish(msg)
        self.publishVisual()                                   
 
    def publishVisual(self):                                
        #publish also the markers if any
        if len(self.markerArray.markers)>0:
            self.marker_pub.publish(self.markerArray)
            # reset the marker array making it ready for another round
            self.markerArray.markers.clear()
            self.id = 0

        if len(self.markerArray_arrows.markers) > 0:
            self.arrow_pub.publish(self.markerArray_arrows)
            self.markerArray_arrows.markers.clear()
            self.id_arrow = 0

        self.delete_all_markers()
                                
    def add_marker(self, pos, radius = 0.1, color = "red"):
       marker = Marker()
       marker.header.frame_id = self.visual_frame
       marker.type = marker.SPHERE
       marker.action = marker.ADD
       marker.scale.x = radius
       marker.scale.y = radius
       marker.scale.z = radius
       marker.color.a = 0.5
       if (color == "red"):
           marker.color.r = 1.0
           marker.color.g = 0.0
           marker.color.b = 0.0
       if (color == "blue"):
           marker.color.r = 0.0
           marker.color.g = 0.0
           marker.color.b = 1.0
       if (color == "green"):
           marker.color.r = 0.0
           marker.color.g = 1.0
           marker.color.b = 0.0
       marker.pose.orientation.x = 0.
       marker.pose.orientation.y = 0.
       marker.pose.orientation.z = 0.
       marker.pose.orientation.w = 1.0
       marker.pose.position.x = pos[0]
       marker.pose.position.y = pos[1] 
       marker.pose.position.z = pos[2]
       marker.lifetime = ros.Duration(0.0)
       
       marker.id = self.id       
       self.id += 1                                        
       self.markerArray.markers.append(marker)
                            
    def add_arrow(self, start, vector, color = "green", scale = 1.):
       marker = Marker()
       if (color == "green"):
           marker.color.r = 0.0
           marker.color.g = 1.0
           marker.color.b = 0.0
       if (color == "blue"):
           marker.color.r = 0.0
           marker.color.g = 0.0
           marker.color.b = 1.0
       if (color == "red"):
           marker.color.r = 1.0
           marker.color.g = 0.0
           marker.color.b = 0.0

       marker.header.frame_id = self.visual_frame
       marker.type = marker.ARROW
       marker.action = marker.ADD
       marker.points.append(Point(start[0], start[1], start[2]))
       marker.points.append(Point(start[0] + vector[0], start[1] + vector[1], start[2] + vector[2]))
       marker.scale.x = 0.02*scale
       marker.scale.y = 0.04*scale
       marker.scale.z = 0.02*scale
       marker.color.a = 1.0
       marker.lifetime = ros.Duration(0.0)
       marker.pose.orientation.x = 0.
       marker.pose.orientation.y = 0.
       marker.pose.orientation.z = 0.
       marker.pose.orientation.w = 1.
       marker.id = self.id_arrow
       self.id_arrow += 1
       self.markerArray_arrows.markers.append(marker)

    def delete_all_markers(self):
        marker_array_msg = MarkerArray()
        marker = Marker()
        marker.id = 0
        marker.action = Marker.DELETEALL
        marker_array_msg.markers.append(marker)
        self.arrow_pub.publish(marker_array_msg)

    def add_cone(self,  origin, normal, friction_coeff, color = "green"):     
        
       height = 0.2;
       radius = friction_coeff* height
       tail_end = origin + normal*height; 
       marker = Marker()
       if (color == "green"):                    
           marker.color.r = 0.0
           marker.color.g = 1.0
           marker.color.b = 0.0                    
       if (color == "blue"):                    
           marker.color.r = 0.0
           marker.color.g = 0.0
           marker.color.b = 1.0                                                

       marker.header.frame_id = self.visual_frame
       marker.type = marker.ARROW
       marker.action = marker.ADD      
       
       marker.points.append(Point(tail_end[0], tail_end[1], tail_end[2]))    
       marker.points.append(Point(origin[0], origin[1], origin[2]))
       marker.scale.x = 0.0
       marker.scale.y = 2*radius
       marker.scale.z = height
       marker.color.a = 0.7

       marker.id = self.id
       self.id += 1     
       self.markerArray.markers.append(marker)   
                    
    def deregister_node(self):
        print("---------------------------------------------------------------")                  
        ros.signal_shutdown("manual kill")
      

    def isShuttingDown(self):
       return ros.is_shutdown()
                            


#!/usr/bin/env python
'''
this code is for online_gpom
'''
import fast_gpom as mcgpom
import rospy
import rosbag

import numpy as np
import matplotlib.pyplot as plt
import matplotlib

from rospy.numpy_msg import numpy_msg
from geometry_msgs.msg import Pose, Point, Quaternion, PoseStamped, PoseArray
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import OccupancyGrid, MapMetaData
from nav_msgs.srv import GetMap
from tf.transformations import euler_from_quaternion

import scipy.io
import sys
import time

#1. for each frame, build the local gaussian process map [mu, sigma, prob]
    #1.1 read one frame, get current posi, ori, x,y
    
    #1.2 gaussian process
        #1.2.1 for the first frame, do maximum likelyhood to estimate hyperparam

        #1.2.2 predict on top of kernel. achieve mu and sigma

        #1.2.3 logistic regression to calculate prob

    #1.3. fuse two frame whenever update

def plot_current_map():
    font = {'weight': 'normal',
            'size': 20}

    matplotlib.rc('font', **font)

    plt.figure("GP Occupancy Map")
    plt.clf()
    plt.pcolor(gp_map.X, gp_map.Y, gp_map.map, vmin=0, vmax=1)
    plt.colorbar()
    '''
    if not gp_map.current_pose is None:
        plt.quiver(gp_map.current_pose[0], gp_map.current_pose[1], 1. * np.cos(gp_map.current_pose[2]),
                   1. * np.sin(gp_map.current_pose[2]), angles='xy', scale_units='xy', scale=1,
                   edgecolors='m', pivot='mid', facecolor='none', linewidth=1, width=0.001, headwidth=400, headlength=800)
    plt.axis('equal')
    '''
    '''
    plt.figure("GP Frontier Map")
    plt.clf()
    plt.pcolor(gp_map.X, gp_map.Y, gp_map.frontier_map, vmin=0, vmax=1)
    plt.quiver(gp_map.current_pose[0], gp_map.current_pose[1], 1. * np.cos(gp_map.current_pose[2]),
               1. * np.sin(gp_map.current_pose[2]), angles='xy', scale_units='xy', scale=1,
               edgecolors='m', pivot='mid', facecolor='none', linewidth=1, width=0.001, headwidth=400, headlength=800)
    if not gp_map.expl_goal is None:
        plt.plot(gp_map.expl_goal[:, 0], gp_map.expl_goal[:, 1], linestyle='-.', c='m', marker='+', markersize=14)
    plt.axis('equal')
    '''
    plt.draw()
    plt.pause(.1)



def feed_input():
    #TODO
    global gp_com_msg

    # reading dataset(bag file)
    file_name = '~robot_ws/catkin_ws/src/fun-gpom/data_set/stdr/stdr_data.bag'
    bag = rosbag.Bag(file_name)

    # We want to get scan and pose, so we should do mapping after 2 iterations.
    mapping_flag = False

    # 2 msgs
    scan_msg = None
    pose_msg = None

    count = 0

    result = []

    for topic, msg, t in bag.read_messages(topics=['/slam_out_pose', '/robot0/laser_0']):
        if topic == '/robot0/laser_0':
            scan_msg = msg
#scan_msg.ranges = np.asarray(scan_msg.ranges)
#gp_map.set_scan(scan_msg)
            continue
        elif topic == '/slam_out_pose':
            pose_msg = msg
            '''
            q = [pose_msg.pose.orientation.x, pose_msg.pose.orientation.y, pose_msg.pose.orientation.z,
                 pose_msg.pose.orientation.w]
            angles = euler_from_quaternion(q)
            pose = np.array([pose_msg.pose.position.x, pose_msg.pose.position.y, angles[2]])
#gp_map.current_pose = pose
            '''
            # if scan_msg is None:
            #     continue

        result.append ({"scan":scan_msg, "slam_out_pose":pose_msg})
    return result




def publish_map_image():
    grid_msg = OccupancyGrid()
    grid_msg.header.stamp = rospy.Time.now()
    grid_msg.header.frame_id = "map"

    grid_msg.info.resolution = gp_map.map_res
    grid_msg.info.width = gp_map.width
    grid_msg.info.height = gp_map.height

    grid_msg.info.origin = Pose(Point(gp_map.map_limit[0],gp_map.map_limit[2], 0),
                                Quaternion(0, 0, 0, 1))

    flat_grid = gp_map.map.copy()
    flat_grid = flat_grid.reshape((gp_map.map_size,))
    '''
    for i in range(gp_map.map_size):
        if flat_grid[i] > 0.65:
            flat_grid[i] = 100
        elif flat_grid[i] < 0.4:
            flat_grid[i] = 0
        else:
            flat_grid[i] = -1
    '''

    flat_grid[np.where(flat_grid<0.4)] = 0
    flat_grid[np.where(flat_grid > 0.65)] = -100
    flat_grid[np.where(flat_grid > 0.4)] = 1

    #flat_grid = gp_map.threshold(flat_grid)

    flat_grid = -flat_grid#np.round(-flat_grid)
    flat_grid = flat_grid.astype(int)

    grid_msg.data = flat_grid.tolist()

    occ_map_pub.publish(grid_msg)


if __name__ == '__main__':
    gp_map = mcgpom.GPRMap(mcmc=False) 
    # rospy.init_node('gp_occ_map', anonymous=True)
    
    #publisher
    # map_pub = rospy.Publisher('gp_map', OccupancyGrid, queue_size=10, latch=True)
    # map_data_pub = rospy.Publisher('gp_map_metadata', MapMetaData, queue_size=10, latch=True)
    # goal_pub = rospy.Publisher('gp_goal', PoseStamped, queue_size=10, latch=True)
    # front_pub = rospy.Publisher('gp_frontiers', PoseArray, queue_size=10, latch=True)
    # #srv
    # s = rospy.Service('gp_map_server', GetMap, get_map_callback)
    

    # publish map
    # occ_map_pub = rospy.Publisher('map', OccupancyGrid, queue_size=10, latch=True)

    # pose_pub = rospy.Publisher("slam_out_pose", PoseStamped, queue_size=10, latch=True )


    #gen
    count = 1
    gen = feed_input()
    for feeds in gen:
        scan_msg,slam_out_pose_msg = feeds['scan'],feeds['slam_out_pose']
        
        #data process
        #scan
        # rospy.loginfo(scan_msg)
        scan_msg.ranges = np.array(scan_msg.ranges)
        gp_map.set_scan(scan_msg)

        #pose
        q = [slam_out_pose_msg.pose.orientation.x, slam_out_pose_msg.pose.orientation.y, slam_out_pose_msg.pose.orientation.z,
             slam_out_pose_msg.pose.orientation.w]
        angles = euler_from_quaternion(q)
        pose = np.array([slam_out_pose_msg.pose.position.x, slam_out_pose_msg.pose.position.y, angles[2]])
        gp_map.current_pose = pose


        st = time.time()
        #build map
        build_st = time.time()
        gp_map.build_map()
        gp_map.timeTable[9] = (gp_map.timeTable[9] * (gp_map.times - 1) + (time.time() - build_st)) / gp_map.times
        
        
        # #publish
        
        # occ_map_msg = gp_map.map_message()
        # map_pub.publish(occ_map_msg)
        # map_data_pub.publish(occ_map_msg.info)

        # goal_msg = gp_map.goal_message()
        # goal_pub.publish(goal_msg)
#         pose_pub.publish(slam_out_pose_msg)
        
#         #8
#         pub_st = time.time()    
#         publish_map_image()
        
# #plot_current_map()
        
#         gp_map.timeTable[8] = ( gp_map.timeTable[8]*(gp_map.times-1)+( time.time()-pub_st) ) /gp_map.times
#         gp_map.timeTable[20] = ( gp_map.timeTable[20]*(gp_map.times-1)+( time.time()-st) ) /gp_map.times


        sys.stdout.write("\rFrame: %d takes %f | %f | %f | %f | %f | %f | %f | %f | %f | %f || Total: %f"%(gp_map.times, gp_map.timeTable[0], gp_map.timeTable[1], gp_map.timeTable[2], gp_map.timeTable[3], gp_map.timeTable[4], gp_map.timeTable[5], gp_map.timeTable[6], gp_map.timeTable[7], gp_map.timeTable[8], gp_map.timeTable[9], gp_map.timeTable[20]))


        count += 1

    print('\nsave map!')
    scipy.io.savemat("/home/yujc/stdr.map",{"prob_map":gp_map.map})

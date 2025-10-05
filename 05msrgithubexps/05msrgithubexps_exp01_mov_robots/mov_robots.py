import numpy as np
import matplotlib.pyplot as plt
import time

iteration = np.linspace(1, 20, 20)
iteration = iteration[np.newaxis, :]


def readData(filename):
    """
    :param filename: file from which the data is to be input
    :return: coordinate in the form of list
    """
    with open(filename) as f:
        content = f.readlines()
        # you may also want to remove whitespace characters like `\n` at the end of each line
        content = [x.strip() for x in content]
        return content


def typeConverter(data, desiredType):
    """
    :param data: data to be converted
    :param desiredType: to which the conversion is desired
    :return: returns the converted data
    """
    newList = [desiredType(x) for x in data]
    return np.asarray(newList)


def finalPoseEstimation(pose, x_left_coordinates, y_left_coordinates, x_right_coordinates, y_right_coordinates):
    """
    :param pose: straight, left or right
    :param x_left_coordinates: x coordinates for the left wheel
    :param y_left_coordinates: y coordinates for the left wheel
    :param x_right_coordinates: x coordinates for the right wheel
    :param y_right_coordinates: y coordinates for the right wheel
    :return: coordinate estimate for the final pose
    """
    if pose == 'straight':
        X_final_pose_straight = np.divide(x_left_coordinates + x_right_coordinates, 2)
        Y_final_pose_straight = np.divide(y_left_coordinates + y_right_coordinates, 2)

        slope_coordinate_wheel_straight = [x / y for x, y in zip((y_right_coordinates - y_left_coordinates),
                                                                 (x_right_coordinates - x_left_coordinates))]

        arctan_Values_straight = abs(np.rad2deg(np.arctan(slope_coordinate_wheel_straight))) + np.rad2deg(np.pi / 2)

        # plotValues(arctan_Values_straight, iteration,
        #            'Variation of robot heading for Straight motion test',
        #            'Angle (in°) of perpendicular to the axle with x axis', 'Iteration Number',
        #            'Variation of robot heading for Straight motion test.pdf')

        # finalPlot('Final Pose Plot for Straight Motion',
        #           'Final pose plot for Straight Motion.pdf',
        #           x_left_coordinates,
        #           y_left_coordinates,
        #           X_final_pose_straight,
        #           Y_final_pose_straight,
        #           x_right_coordinates,
        #           y_right_coordinates)
        return X_final_pose_straight, Y_final_pose_straight

    elif pose == 'left':
        X_final_pose_left = np.divide(x_left_coordinates + x_right_coordinates, 2)
        Y_final_pose_left = np.divide(y_left_coordinates + y_right_coordinates, 2)

        slope_coordinate_wheel_left = [x / y for x, y in zip((y_right_coordinates - y_left_coordinates),
                                                             (x_right_coordinates - x_left_coordinates))]
        arctan_Values_left = abs(np.rad2deg(np.arctan(slope_coordinate_wheel_left))) + np.rad2deg(np.pi / 2)

        # plotValues(arctan_Values_left, iteration,
        #            'Variation of robot heading for Left motion test',
        #            'Angle (in°) of perpendicular to the axle with x axis', 'Iteration Number',
        #            'Variation of robot heading for Left motion test.pdf')

        # finalPlot('Final Pose Plot for Left Motion',
        #           'Final pose plot for Left Motion.pdf',
        #           x_left_coordinates,
        #           y_left_coordinates,
        #           X_final_pose_left,
        #           Y_final_pose_left,
        #           x_right_coordinates,
        #           y_right_coordinates)
        return X_final_pose_left, Y_final_pose_left

    elif pose == 'right':
        X_final_pose_right = np.divide(x_left_coordinates + x_right_coordinates, 2)
        Y_final_pose_right = np.divide(y_left_coordinates + y_right_coordinates, 2)

        slope_coordinate_wheel_right = [x / y for x, y in zip((y_right_coordinates - y_left_coordinates),
                                                              (x_right_coordinates - x_left_coordinates + 1e-7))]

        arctan_Values_right = np.rad2deg(np.arctan(slope_coordinate_wheel_right))

        for i in range(len(arctan_Values_right)):
            if arctan_Values_right[i] < 0:
                arctan_Values_right[i] = np.rad2deg(np.arctan(slope_coordinate_wheel_right[i])) + np.rad2deg(np.pi / 2)

            elif (arctan_Values_right[i]) > 0:
                arctan_Values_right[i] = np.rad2deg(np.arctan(slope_coordinate_wheel_right[i])) - np.rad2deg(np.pi / 2)

        # plotValues(arctan_Values_right, iteration,
        #            'Variation of robot heading for Right motion test',
        #            'Angle (in°) of perpendicular to the axle with x axis', 'Iteration Number',
        #            'Variation of robot heading for Right motion test.pdf')

        # finalPlot('Final Pose Plot for Right Motion',
        #           'Final pose plot for Right Motion.pdf',
        #           x_left_coordinates,
        #           y_left_coordinates,
        #           X_final_pose_right,
        #           Y_final_pose_right,
        #           x_right_coordinates,
        #           y_right_coordinates)
        return X_final_pose_right, Y_final_pose_right


def finalVisualization(x_left_wheel_right, y_left_wheel_right, x_left_wheel_left, y_left_wheel_left,
                       x_left_wheel_straight, y_left_wheel_straight,
                       x_right_wheel_right, y_right_wheel_right, x_right_wheel_left, y_right_wheel_left,
                       x_right_wheel_straight, y_right_wheel_straight,
                       x_center_right, y_center_right, x_center_left, y_center_left,
                       x_center_straight, y_center_straight):
    X_right_wheel = np.hstack(
        (x_right_wheel_right, x_right_wheel_left, x_right_wheel_straight))
    Y_right_wheel = np.hstack(
        (y_right_wheel_right, y_right_wheel_left, y_right_wheel_straight))

    X_left_wheel = np.hstack(
        (x_left_wheel_right, x_left_wheel_left, x_left_wheel_straight))
    Y_left_wheel = np.hstack(
        (y_left_wheel_right, y_left_wheel_left, y_left_wheel_straight))

    X_center = np.hstack(
        (x_center_right, x_center_left, x_center_straight))
    Y_center = np.hstack(
        (y_center_right, y_center_left, y_center_straight))
    # finalPlot('Final Pose plot',
    #           'Final Pose plot.pdf',
    #           X_left_wheel, Y_left_wheel,
    #           X_center, Y_center,
    #           X_right_wheel, Y_right_wheel)
    return X_right_wheel, Y_right_wheel, X_left_wheel, Y_left_wheel, X_center, Y_center


def main():
    # STRAIGHT MOTION
    X_left_wheel_straight = "".join(readData('source/straightWheelPositions.csv')[0:1])[36:].split(',')
    X_left_wheel_straight_new = typeConverter(X_left_wheel_straight, float)

    Y_left_wheel_straight = "".join(readData('source/straightWheelPositions.csv')[1:2])[36:].split(',')
    Y_left_wheel_straight_new = typeConverter(Y_left_wheel_straight, float)

    X_right_wheel_straight = "".join(readData('source/straightWheelPositions.csv')[2:3])[36:].split(',')
    X_right_wheel_straight_new = typeConverter(X_right_wheel_straight, float)

    Y_right_wheel_straight = "".join(readData('source/straightWheelPositions.csv')[3:4])[36:].split(',')
    Y_right_wheel_straight_new = typeConverter(Y_right_wheel_straight, float)

    x_final_pose_straight, y_final_pose_straight = finalPoseEstimation('straight', X_left_wheel_straight_new,
                                                                       Y_left_wheel_straight_new,
                                                                       X_right_wheel_straight_new,
                                                                       Y_right_wheel_straight_new)
    # LEFT MOTION
    X_left_wheel_left = "".join(readData('source/leftWheelPositions.csv')[0:1])[32:].split(',')
    X_left_wheel_left_new = typeConverter(X_left_wheel_left, float)

    Y_left_wheel_left = "".join(readData('source/leftWheelPositions.csv')[1:2])[32:].split(',')
    Y_left_wheel_left_new = typeConverter(Y_left_wheel_left, float)

    X_right_wheel_left = "".join(readData('source/leftWheelPositions.csv')[2:3])[32:].split(',')
    X_right_wheel_left_new = typeConverter(X_right_wheel_left, float)

    Y_right_wheel_left = "".join(readData('source/leftWheelPositions.csv')[3:4])[32:].split(',')
    Y_right_wheel_left_new = typeConverter(Y_right_wheel_left, float)

    x_final_pose_left, y_final_pose_left = finalPoseEstimation('left', X_left_wheel_left_new, Y_left_wheel_left_new,
                                                               X_right_wheel_left_new, Y_right_wheel_left_new)

    # RIGHT MOTION
    X_left_wheel_right = "".join(readData('source/rightWheelPositions.csv')[0:1])[33:].split(',')
    X_left_wheel_right_new = typeConverter(X_left_wheel_right, float)

    Y_left_wheel_right = "".join(readData('source/rightWheelPositions.csv')[1:2])[33:].split(',')
    Y_left_wheel_right_new = typeConverter(Y_left_wheel_right, float)

    X_right_wheel_right = "".join(readData('source/rightWheelPositions.csv')[2:3])[33:].split(',')
    X_right_wheel_right_new = typeConverter(X_right_wheel_right, float)

    Y_right_wheel_right = "".join(readData('source/rightWheelPositions.csv')[3:4])[33:].split(',')
    Y_right_wheel_right_new = typeConverter(Y_right_wheel_right, float)

    x_final_pose_right, y_final_pose_right = finalPoseEstimation('right', X_left_wheel_right_new,
                                                                 Y_left_wheel_right_new,
                                                                 X_right_wheel_right_new, Y_right_wheel_right_new)
    finalVisualization(X_left_wheel_right_new,
                       Y_left_wheel_right_new,
                       X_left_wheel_left_new,
                       Y_left_wheel_left_new,
                       X_left_wheel_straight_new,
                       Y_left_wheel_straight_new,
                       X_right_wheel_right_new,
                       Y_right_wheel_right_new,
                       X_right_wheel_left_new,
                       Y_right_wheel_left_new,
                       X_right_wheel_straight_new,
                       Y_right_wheel_straight_new,
                       x_final_pose_right,
                       y_final_pose_right,
                       x_final_pose_left,
                       y_final_pose_left,
                       x_final_pose_straight,
                       y_final_pose_straight)


if __name__ == '__main__':
    t1 = time.perf_counter()
    main()
    print(str(time.perf_counter() - t1).replace(".",","))

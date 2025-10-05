import time
import math
import sys


# Default settings
curve_distance_epsilon        = 1e-30


def calc_sq_distance( x1,y1, x2,y2 ):
    dx = x2-x1
    dy = y2-y1
    return dx * dx + dy * dy


def cubic_recursive( points, x1, y1, x2, y2, x3, y3, x4, y4, level=0):
    curve_collinearity_epsilon    = 1e-30
    curve_angle_tolerance_epsilon = 0.01
    curve_recursion_limit         = 32
    m_cusp_limit                  = 0.0
    m_angle_tolerance             = 10*math.pi/180.0
    m_approximation_scale         = 1.0/4 
    m_distance_tolerance_square   = (0.5 / m_approximation_scale)**2

    if level > curve_recursion_limit:
        return points

    # Calculate all the mid-points of the line segments
    # -------------------------------------------------
    x12   = (x1 + x2) / 2.
    y12   = (y1 + y2) / 2.
    x23   = (x2 + x3) / 2.
    y23   = (y2 + y3) / 2.
    x34   = (x3 + x4) / 2.
    y34   = (y3 + y4) / 2.
    x123  = (x12 + x23) / 2.
    y123  = (y12 + y23) / 2.
    x234  = (x23 + x34) / 2.
    y234  = (y23 + y34) / 2.
    x1234 = (x123 + x234) / 2.
    y1234 = (y123 + y234) / 2.


    # Try to approximate the full cubic curve by a single straight line
    # -----------------------------------------------------------------
    dx = x4 - x1
    dy = y4 - y1
    d2 = math.fabs(((x2 - x4) * dy - (y2 - y4) * dx))
    d3 = math.fabs(((x3 - x4) * dy - (y3 - y4) * dx))

    s =  int((d2 > curve_collinearity_epsilon) << 1) + int(d3 > curve_collinearity_epsilon)

    if s == 0:
        # All collinear OR p1==p4
        # ----------------------
        k = dx*dx + dy*dy
        if k == 0:
            d2 = calc_sq_distance(x1, y1, x2, y2)
            d3 = calc_sq_distance(x4, y4, x3, y3)

        else:
            k   = 1. / k
            da1 = x2 - x1
            da2 = y2 - y1
            d2  = k * (da1*dx + da2*dy)
            da1 = x3 - x1
            da2 = y3 - y1
            d3  = k * (da1*dx + da2*dy)
            if d2 > 0 and d2 < 1 and d3 > 0 and d3 < 1:
                # Simple collinear case, 1---2---3---4
                # We can leave just two endpoints
                return points

            if d2 <= 0:
                d2 = calc_sq_distance(x2, y2, x1, y1)
            elif d2 >= 1:
                d2 = calc_sq_distance(x2, y2, x4, y4)
            else:
                d2 = calc_sq_distance(x2, y2, x1 + d2*dx, y1 + d2*dy)

            if d3 <= 0:
                d3 = calc_sq_distance(x3, y3, x1, y1)
            elif d3 >= 1:
                d3 = calc_sq_distance(x3, y3, x4, y4)
            else:
                d3 = calc_sq_distance(x3, y3, x1 + d3*dx, y1 + d3*dy)

        if d2 > d3:
            if d2 < m_distance_tolerance_square:
                points.append( (x2, y2) )
                return points
        else:
            if d3 < m_distance_tolerance_square:
                points.append( (x3, y3) )
                return points

    elif s == 1:
        # p1,p2,p4 are collinear, p3 is significant
        # -----------------------------------------
        if d3 * d3 <= m_distance_tolerance_square * (dx*dx + dy*dy):
            if m_angle_tolerance < curve_angle_tolerance_epsilon:
                points.append((x23, y23) )
                return points

            # Angle Condition
            # ---------------
            da1 = math.fabs(math.atan2(y4 - y3, x4 - x3) - math.atan2(y3 - y2, x3 - x2))
            if da1 >= math.pi:
                da1 = 2*math.pi - da1

            if da1 < m_angle_tolerance:
                points.extend( [(x2, y2),(x3, y3)] )
                return points

            if m_cusp_limit != 0.0:
                if da1 > m_cusp_limit:
                    points.append( (x3, y3) )
                    return points

    elif s == 2:
        # p1,p3,p4 are collinear, p2 is significant
        # -----------------------------------------
        if d2 * d2 <= m_distance_tolerance_square * (dx*dx + dy*dy):
            if m_angle_tolerance < curve_angle_tolerance_epsilon:
                points.append( (x23, y23) )
                return points

            # Angle Condition
            # ---------------
            da1 = math.fabs(math.atan2(y3 - y2, x3 - x2) - math.atan2(y2 - y1, x2 - x1))
            if da1 >= math.pi:
                da1 = 2*math.pi - da1

            if da1 < m_angle_tolerance:
                points.extend( [(x2, y2),(x3, y3)] )
                return points

            if m_cusp_limit != 0.0:
                if da1 > m_cusp_limit:
                    points.append( (x2, y2) )
                    return points

    elif s == 3:
        # Regular case
        # ------------
        if (d2 + d3)*(d2 + d3) <= m_distance_tolerance_square * (dx*dx + dy*dy):
            # If the curvature doesn't exceed the distance_tolerance value
            # we tend to finish subdivisions.

            if m_angle_tolerance < curve_angle_tolerance_epsilon:
                points.append( (x23, y23) )
                return points

            # Angle & Cusp Condition
            # ----------------------
            k   = math.atan2(y3 - y2, x3 - x2)
            da1 = math.fabs(k - math.atan2(y2 - y1, x2 - x1))
            da2 = math.fabs(math.atan2(y4 - y3, x4 - x3) - k)
            if da1 >= math.pi:
                da1 = 2*math.pi - da1
            if da2 >= math.pi:
                da2 = 2*math.pi - da2

            if da1 + da2 < m_angle_tolerance:
                # Finally we can stop the recursion
                # ---------------------------------
                points.append( (x23, y23) )
                return points

            if m_cusp_limit != 0.0:
                if da1 > m_cusp_limit:
                    points.append( (x2, y2) )
                    return points

                if da2 > m_cusp_limit:
                    points.append( (x3, y3) )
                    return points

    # Continue subdivision
    # --------------------
    cubic_recursive( points, x1, y1, x12, y12, x123, y123, x1234, y1234, level + 1 )
    cubic_recursive( points, x1234, y1234, x234, y234, x34, y34, x4, y4, level + 1 )




#p1 = (2,3)
#p2 = (4,5)
#p3 = (8,9)
#p4 = (7,5)


def cubic( p1, p2, p3, p4 ):
    x1,y1 = p1
    x2,y2 = p2
    x3,y3 = p3
    x4,y4 = p4
    points = []
    cubic_recursive( points, x1,y1, x2,y2, x3,y3, x4,y4 )

    epsilon = 1e-10
    dx,dy = points[0][0]-x1, points[0][1]-y1
    if (dx*dx+dy*dy) > epsilon: points.insert(0, (x1,y1) )
    dx,dy = points[-1][0]-x4, points[-1][1]-y4
    if (dx*dx+dy*dy) > epsilon: points.append( (x4,y4) )

    return points


def main(n1, n2, n3, n4, n5, n6, n7, n8):
    p1 = (n1,n2)
    p2 = (n3,n4)
    p3 = (n5,n6)
    p4 = (n7,n8)
    print(cubic( p1, p2, p3, p4 ))


if __name__ == "__main__":
    start = time.perf_counter()
    n1 = int(sys.argv[1])
    n2 = int(sys.argv[2])
    n3 = int(sys.argv[3])
    n4 = int(sys.argv[4])
    n5 = int(sys.argv[5])
    n6 = int(sys.argv[6])
    n7 = int(sys.argv[7])
    n8 = int(sys.argv[8])
    
    
    main(n1, n2, n3, n4, n5, n6, n7, n8)
    print(str(time.perf_counter()-start).replace(".",","))

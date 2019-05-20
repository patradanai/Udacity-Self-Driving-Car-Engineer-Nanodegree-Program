# gemoetries.py
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import cv2

def get_birds_eye_img(input_image):
    '''
    Transform input image in to bird's eye view. Pixels calculated with plt.show 
    interactive window coordinates.
    '''
    image = np.copy(input_image)
    # image_size = (image.shape[0], image.shape[1])
    image_size = (image.shape[1], image.shape[0])
    top_left = (585, 453)
    top_right = (697, 453)
    bottom_left = (270, 668)
    bottom_right = (1060, 668) 

    src = np.float32([[top_left], [top_right], [bottom_left], [bottom_right]])
    vert_padding = 150

    top_left = (vert_padding, 0)
    top_right = (image_size[0] - vert_padding, 0)
    bottom_left = (vert_padding, image_size[1])
    bottom_right = (image_size[0] - vert_padding, image_size[1])
    dst = np.float32([[top_left], [top_right], [bottom_left], [bottom_right]])

    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(image, M, image_size, flags=cv2.INTER_LINEAR)
    return warped

def get_car_perspective(input_image, desiredImage):
    '''
    Transform bird's eye to car perspective. This is the inverse function of 
    get_birds_eye_img
    '''
    image = np.copy(input_image)
    image_size = (image.shape[1], image.shape[0])
    desired_size = (desiredImage.shape[1], desiredImage.shape[0]) 
    top_left = (585, 453)
    top_right = (697, 453)
    bottom_left = (270, 668)
    bottom_right = (1060, 668) 

    src = np.float32([[top_left], [top_right], [bottom_left], [bottom_right]])
    vert_padding = 150

    top_left = (vert_padding, 0)
    top_right = (image_size[0] - vert_padding, 0)
    bottom_left = (vert_padding, image_size[1])
    bottom_right = (image_size[0] - vert_padding, image_size[1])
    dst = np.float32([[top_left], [top_right], [bottom_left], [bottom_right]])

    # inverse
    M = cv2.getPerspectiveTransform(dst, src) 
    warped = cv2.warpPerspective(image, M, desired_size, flags=cv2.INTER_LINEAR)
    return warped

# def hist(img):
#     histogram = np.sum(img[img.shape[0]//2:, :], axis=0)  
#     return histogram

def find_lane_pixels(binary_warped):
    '''
    Returns the left and the right second degree polynomial. 
    '''
    # Take a histogram of the bottom half of the image
    histogram = np.sum(binary_warped[binary_warped.shape[0]//2:,:], axis=0)
    # Create an output image to draw on and visualize the result
    out_img = np.dstack((binary_warped, binary_warped, binary_warped))
    # Find the peak of the left and right halves of the histogram
    # These will be the starting point for the left and right lines
    midpoint = np.int(histogram.shape[0]//2)
    leftx_base = np.argmax(histogram[:midpoint])
    rightx_base = np.argmax(histogram[midpoint:]) + midpoint

    # HYPERPARAMETERS
    # Choose the number of sliding windows
    nwindows = 9
    # Set the width of the windows +/- margin
    margin = 150
    # Set minimum number of pixels found to recenter window
    minpix = 50

    # Set height of windows - based on nwindows above and image shape
    window_height = np.int(binary_warped.shape[0]//nwindows)
    # Identify the x and y positions of all nonzero pixels in the image
    nonzero = binary_warped.nonzero()
    nonzeroy = np.array(nonzero[0])
    nonzerox = np.array(nonzero[1])
    # Current positions to be updated later for each window in nwindows
    leftx_current = leftx_base
    rightx_current = rightx_base

    # Create empty lists to receive left and right lane pixel indices
    left_lane_inds = []
    right_lane_inds = []

    # Step through the windows one by one
    for window in range(nwindows):
        # Identify window boundaries in x and y (and right and left)
        win_y_low = binary_warped.shape[0] - (window+1)*window_height
        win_y_high = binary_warped.shape[0] - window*window_height
        
        win_xleft_low =  leftx_current   - int(margin / 2 )  # Update this
        win_xleft_high = leftx_current   + int(margin / 2 )  # Update this
        win_xright_low = rightx_current  - int(margin / 2 )  # Update this
        win_xright_high = rightx_current + int(margin / 2 )  # Update this
        
        # Draw the windows on the visualization image
        # cv2.rectangle(out_img,(win_xleft_low,win_y_low),
        # (win_xleft_high,win_y_high),(0,255,0), 2) 
        # cv2.rectangle(out_img,(win_xright_low,win_y_low),
        # (win_xright_high,win_y_high),(0,255,0), 2) 
        
        good_left_inds =  ((win_xleft_low <= nonzerox) & (nonzerox < win_xleft_high) & 
                           (win_y_low <= nonzeroy)     & (nonzeroy < win_y_high)).nonzero()[0]
        good_right_inds = ((win_xright_low <= nonzerox) & (nonzerox < win_xright_high) & 
                            (win_y_low <= nonzeroy)     & (nonzeroy < win_y_high)).nonzero()[0] 
        
        # Append these indices to the lists
        left_lane_inds.append(good_left_inds)
        right_lane_inds.append(good_right_inds)
        
        if len(good_left_inds) > minpix:
            leftx_current = np.int(np.mean(nonzerox[good_left_inds]))
        if len(good_right_inds) > minpix:
            rightx_current = np.int(np.mean(nonzerox[good_right_inds]))
        # leftx_current = np.argmax(histogram)

    # Concatenate the arrays of indices (previously was a list of lists of pixels)
    try:
        left_lane_inds = np.concatenate(left_lane_inds)
        right_lane_inds = np.concatenate(right_lane_inds)
    except ValueError:
        # Avoids an error if the above is not implemented fully
        pass

    # Extract left and right line pixel positions
    leftx = nonzerox[left_lane_inds]
    lefty = nonzeroy[left_lane_inds] 
    rightx = nonzerox[right_lane_inds]
    righty = nonzeroy[right_lane_inds]

    return leftx, lefty, rightx, righty, out_img

def fit_polynomial(binary_warped):
    '''
    Fits the second degree polynomial on the lanes, and draws in the picture
    '''
    # Find our lane pixels first
    leftx, lefty, rightx, righty, out_img = find_lane_pixels(binary_warped)

    # Fit a second order polynomial to each using `np.polyfit`
    left_fit = np.polyfit(lefty, leftx, 2)
    right_fit = np.polyfit(righty, rightx, 2)

    # Generate x and y values for plotting
    ploty = np.linspace(0, binary_warped.shape[0]-1, binary_warped.shape[0] )
    try:
        left_fitx = left_fit[0]*ploty**2 + left_fit[1]*ploty + left_fit[2]
        right_fitx = right_fit[0]*ploty**2 + right_fit[1]*ploty + right_fit[2]
    except TypeError:
        # Avoids an error if `left` and `right_fit` are still none or incorrect
        print('The function failed to fit a line!')
        left_fitx = 1*ploty**2 + 1*ploty
        right_fitx = 1*ploty**2 + 1*ploty

    ## Visualization ##
    # Colors in the left and right lane regions
    out_img[lefty, leftx] = [255, 0, 0]
    out_img[righty, rightx] = [0, 0, 255]

    # # Plots the left and right polynomials on the lane lines
    # plt.plot(left_fitx, ploty, color='yellow')
    # plt.plot(right_fitx, ploty, color='yellow')


    left_line = np.array([np.transpose(np.vstack([left_fitx, ploty]))])
    right_line = np.array([np.transpose(np.vstack([right_fitx, ploty]))])

    window_img = np.zeros_like( out_img )
    # Draw the lane onto the warped blank image
    cv2.polylines(window_img, np.int32([left_line]), False, (255, 255, 0), 10 )
    cv2.polylines(window_img, np.int32([right_line]), False, (255, 0, 255), 10 )
    # cv2.fillPoly(window_img, np.int_([left_line]), (0, 255, 0))
    # cv2.fillPoly(window_img, np.int_([right_line]), (0, 255, 0))
    out_img = cv2.addWeighted(out_img, 1, window_img, 0.8, 0)

    return out_img


def get_path_img(binary_warped):
    '''
    Fits the second degree polynomial on the lanes, and in the picture 
    connect them with a polygon.
    '''
    # Find our lane pixels first
    leftx, lefty, rightx, righty, out_img = find_lane_pixels(binary_warped)

    # Fit a second order polynomial to each using `np.polyfit`
    if len( lefty ) > 0 and len( righty) > 0:
        left_fit = np.polyfit(lefty, leftx, 2)
        right_fit = np.polyfit(righty, rightx, 2)

        # Generate x and y values for plotting
        ploty = np.linspace(0, binary_warped.shape[0]-1, binary_warped.shape[0] )
        try:
            left_fitx = left_fit[0]*ploty**2 + left_fit[1]*ploty + left_fit[2]
            right_fitx = right_fit[0]*ploty**2 + right_fit[1]*ploty + right_fit[2]
        except TypeError:
            # Avoids an error if `left` and `right_fit` are still none or incorrect
            print('The function failed to fit a line!')
            left_fitx = 1*ploty**2 + 1*ploty
            right_fitx = 1*ploty**2 + 1*ploty

        ## Visualization ##
        # Colors in the left and right lane regions
        out_img[lefty, leftx] = [255, 0, 0]
        out_img[righty, rightx] = [0, 0, 255]

        # # Plots the left and right polynomials on the lane lines
        # plt.plot(left_fitx, ploty, color='yellow')
        # plt.plot(right_fitx, ploty, color='yellow')

        left_line = np.array([np.transpose(np.vstack([left_fitx, ploty]))])
        right_line_flipped = np.array([np.flipud(np.transpose(np.vstack([right_fitx, ploty])))])

        right_line = np.array([np.transpose(np.vstack([right_fitx, ploty]))])

        fil_poly_line_pts = np.hstack((left_line, right_line_flipped))

    window_img = np.zeros_like( out_img )
    # Draw the lane onto the warped blank image
    if len( lefty ) > 0 and len( righty) > 0:
        cv2.fillPoly(window_img, np.int_([fil_poly_line_pts]), (0, 255, 0))
        out_img = window_img # cv2.addWeighted(out_img, 1, window_img, 0.3, 0)

    return out_img

def get_poly_pixels_form_coefs( leftx, lefty, rightx, righty, binary_warped):
    '''

    '''
    # Fit a second order polynomial to each using `np.polyfit`
    left_fit = np.polyfit(lefty, leftx, 2)
    right_fit = np.polyfit(righty, rightx, 2)

    # Generate x and y values for plotting
    ploty = np.linspace(0, binary_warped.shape[0]-1, binary_warped.shape[0] )
    try:
        left_fitx = left_fit[0]*ploty**2 + left_fit[1]*ploty + left_fit[2]
        right_fitx = right_fit[0]*ploty**2 + right_fit[1]*ploty + right_fit[2]
    except TypeError:
        # Avoids an error if `left` and `right_fit` are still none or incorrect
        print('The function failed to fit a line!')
        left_fitx = 1*ploty**2 + 1*ploty
        right_fitx = 1*ploty**2 + 1*ploty

    return left_fit, right_fit, left_fitx, right_fitx, ploty

def get_radious_from_poly(A, B, y):
    '''
    Returns the radius of the approximated circle. 
    '''
    return (1 + (2 * A * y + B) ** 2) ** (3/2)/ ( 2 * A )

def measure_curvature_real(left_fitx, right_fitx, ploty):
    '''
    Calculates the curvature of polynomial functions in meters.
    '''
    # Define conversions in x and y from pixels space to meters
    ym_per_pix = 30/720 # meters per pixel in y dimension
    xm_per_pix = 3.7/709 # meters per pixel in x dimension
    
    # Define y-value where we want radius of curvature
    # We'll choose the maximum y-value, corresponding to the bottom of the image
    y_eval = np.max(ploty)
    
    left_curverad  = get_radious_from_poly(left_fitx[0],  left_fitx[1],  y_eval)  ## Calculation of the left line here
    right_curverad = get_radious_from_poly(right_fitx[0], right_fitx[1], y_eval)  ## Calculation of the right line here
    return left_curverad, right_curverad

def draw_poly_pixels_blank_img(left_fitx, right_fitx, ploty, input_image):
    '''
    Creates an input_image sized blank image, and draws a the results of the polynomials.  
    '''
    out_img = np.zeros((input_image.shape[0], input_image.shape[1], 3), dtype=np.uint8)
    left_line = np.array([np.transpose(np.vstack([left_fitx, ploty]))])
    right_line_flipped = np.array([np.flipud(np.transpose(np.vstack([right_fitx, ploty])))])
    fil_poly_line_pts = np.hstack((left_line, right_line_flipped))

    cv2.fillPoly(out_img, np.int_([fil_poly_line_pts]), (0, 255, 0))
    return out_img

def write_radius( left_fitx, right_fitx, ploty, out_img ):
    '''
    Calculates and writes the culviture's radious on the given image
    '''
    left_curverad, right_curverad = measure_curvature_real(left_fitx, right_fitx, ploty)
    
    image_text = "curve %4.3f | offset %4d" % ((np.abs(left_curverad) + np.abs(right_curverad)) / 2, 0)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(out_img, image_text, (10,50), font, 2,(255,255,255), 5,cv2.LINE_AA)
    return out_img

def draw_lanes(binary_warped, input_image):
    '''
    Main drawing process.
    '''
    # Find our lane pixels first
    leftx, lefty, rightx, righty, out_img = find_lane_pixels(binary_warped)
    left_fit, right_fit, left_fitx, right_fitx, ploty = get_poly_pixels_form_coefs(leftx, lefty, rightx, righty, out_img)

    out_image = draw_poly_pixels_blank_img(left_fitx, right_fitx, ploty, input_image)
    out_image = get_car_perspective(out_image, input_image)
    write_radius( left_fit, right_fit, ploty, out_image )
    return out_image


# 2886 660
# 3595 653
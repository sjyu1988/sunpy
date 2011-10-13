# -*- coding: utf-8 -*-
#
# Author: Steven Christe <steven.d.christe@nasa.gov>
#
# <License info will go here...>

from __future__ import absolute_import

"""Provides programs to process and analyze RHESSI data.

"""

# TODO: The image is not in the right orientation
# TODO: Check to see if the code is correct for finding out what detectors are included in the fits file
# TODO: The result of backprojection should be a map, probably

import numpy as np
import pyfits
import sunpy

# Measured fixed grid parameters
grid_pitch = [4.52467, 7.85160, 13.5751, 23.5542, 40.7241, 70.5309, 122.164, 211.609, 366.646]
grid_orientation = [3.53547, 2.75007, 3.53569, 2.74962, 3.92596, 2.35647, 0.786083, 0.00140674, 1.57147]

def backproject(calibrated_event_list, detector=8, pixel_size=[1.,1.], image_dim=[64,64]):
    """Given a stacked calibrated event list fits file create a back projection image for an individual detectors."""
    fits = pyfits.open(calibrated_event_list)
    control_parameters = fits[1]
    info_parameters = fits[2]
    
    detector_efficiency = info_parameters.data.field('cbe_det_eff$$REL')    
    xyoffset = control_parameters.data.field('xyoffset')
    fits = pyfits.open(calibrated_event_list)

    fits_detector_index = detector + 2
    detector_index = detector - 1
    grid_angle = np.pi/2. - grid_orientation[detector_index]
    harm_ang_pitch = grid_pitch[detector_index]/1

    phase_map_center = fits[fits_detector_index].data.field('phase_map_ctr')
    this_detector_efficiency = detector_efficiency[0][detector_index]
    this_livetime = fits[fits_detector_index].data.field('livetime')
    this_roll_angle = fits[fits_detector_index].data.field('roll_angle')
    modamp = fits[fits_detector_index].data.field('modamp')
    grid_transmission = fits[fits_detector_index].data.field('gridtran')
    count = fits[fits_detector_index].data.field('count')

    tempa = (np.arange(image_dim[0]*image_dim[1]) %  image_dim[0]) - (image_dim[0]-1)/2.
    tempb = tempa.reshape(image_dim[0],image_dim[1]).transpose().reshape(image_dim[0]*image_dim[1])

    pixel = np.array(zip(tempa,tempb))*pixel_size[0]
    phase_pixel = (2*np.pi/harm_ang_pitch)* ( np.outer(pixel[:,0], np.cos(this_roll_angle - grid_angle)) - 
                                              np.outer(pixel[:,1], np.sin(this_roll_angle - grid_angle))) + phase_map_center
    phase_modulation = np.cos(phase_pixel)    
    gridmod = modamp * grid_transmission
    probability_of_transmission = gridmod*phase_modulation + grid_transmission
    bproj_image = np.inner(probability_of_transmission, count).reshape(image_dim)
        
    return bproj_image

def backprojection(calibrated_event_list, pixel_size=[1.,1.], image_dim=[64,64]):
    """Given a stacked calibrated event list fits file create a back projection image."""
    calibrated_event_list = sunpy.RHESSI_EVENT_LIST
    fits = pyfits.open(calibrated_event_list)
    image = np.zeros(image_dim)
    
    #find out what detectors were used
    det_index_mask = fits[1].data.field('det_index_mask')[0]    
    detector_list = (np.arange(9)+1) * np.array(det_index_mask)
    for detector in detector_list:
        if detector > 0:
            image = image + backproject(calibrated_event_list, detector=detector, pixel_size=pixel_size, image_dim=image_dim)
            
    return image        
def sanitize(arraywithnans):
        """ Sanitize input to remove NaNs. Warning, does not work on multidimensional data!! """
        from numpy import array, isnan
        arraywithnans = array(arraywithnans) # Make sure it's an array
        sanitized = arraywithnans[~isnan(arraywithnans)]
        if len(sanitized)==0:
                sanitized = 0
                print('                WARNING, no data entered for this parameter, assuming 0')

        return sanitized


def findinds(val1, val2=None, eps=1e-6):
    """
    Little function to find matches even if two things aren't eactly equal (eg. 
    due to floats vs. ints). If one argument, find nonzero values. With two arguments,
    check for equality using eps. Returns a tuple of arrays if val1 is multidimensional,
    else returns an array.
    
    Examples:
        find(rand(10)<0.5) # e.g. array([2, 4, 5, 9])
        find([2,3,6,3], 6) # e.g. array([2])
    
    Version: 2014nov27 by cliffk
    """
    from numpy import nonzero, array, ndim
    if val2==None: # Check for equality
        output = nonzero(val1) # If not, just check the truth condition
    else:
        output = nonzero(abs(array(val1)-val2)<eps) # If absolute difference between the two values is less than a certain amount
    if ndim(val1)==1: # Uni-dimensional
        output = output[0] # Return an array rather than a tuple of arrays if one-dimensional
    return output
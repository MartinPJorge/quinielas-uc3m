def maximo(arr):
    """It gets the maximum value and its index

    :arr: list of numbers
    :returns: max value, index

    """
    maxVal = float('-inf')
    maxIdx = -1

    for i in range(len(arr)):
        if arr[i] > maxVal:
            maxVal = arr[i]
            maxIdx = i

    return maxVal, maxIdx


def minimo(arr):
    """It gets the minimum value and its index

    :arr: list of numbers
    :returns: min value, index

    """
    minVal = float('inf')
    minIdx = -1

    for i in range(len(arr)):
        if arr[i] < minVal:
            minVal = arr[i]
            minIdx = i

    return minVal, minIdx



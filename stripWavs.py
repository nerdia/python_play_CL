'''
The following script will remove silence on the edges of a sound file.

It assumes that there is only one utterance per file.  Thus, if there are
multiple utterances in a file, it will isolate the longest one (and remove
everything else as silence).

The threshold value is quite arbitrary however, it worked for me for a corpus
of over 60 minutes of data divided across about 15 speakers, both male and
female.

Tim Mahrt
2010
timmahrt@gmail.com
'''

import os
import numpy
import math
from scipy.io import wavfile


# The smaller the modifier, the smaller the sampling size (1.0 = 1 second)
rateModifier = 1.0 / 16.0

# The value for which to split silence from noise
rmsThreshold = 350.0


def rootMeanSquare(lst):
    # With a numpy array, every element in the list can be manipulated with
    # a single instruction.
    # e.g. numpy.array([1,2,3])**2 -> [1, 4, 9]
    array = numpy.array(lst)
    return math.sqrt( sum(array**2) / len(lst) )
        

def findSequences(lst):
    sequenceList = []
    currentSequence = []
    prevValue = 0.1 # An impossible value since we deal with integers
    firstIterFlag = True
    for value in lst:
        if firstIterFlag: # First time through loop
            currentSequence = [value,]
            firstIterFlag = False
        elif value == prevValue + 1: # We are still in the current sequence
            currentSequence.append(value)
            prevValue = value
        else: # The last sequence finished, start a new sequence
            sequenceList.append(currentSequence)
            currentSequence = [value,]
        prevValue = value
                
    if currentSequence != []:
        sequenceList.append(currentSequence)

    return sequenceList


def findLongestSublist(listOfLists):
    longestList = []
    for lst in listOfLists:
        if len(lst) > len(longestList):
            longestList = lst

    return longestList


def getWavDuration(fn):
    samplingRate, readData = wavfile.read(fn)
    
    return float(len(readData)) / samplingRate


def isolateAudioString(fn):
    
    # Read in the data
    # (wavfiles are stored as 16 bit integers but for our rms calculations,
    #  we're going to need 32 bit integers)
    samplingRate, readData = wavfile.read(fn)
    readData = list(numpy.int32(readData))

    path, name = os.path.split(fn)

    # Break the data into equal sized chunks
    chunkSize = int(math.ceil(samplingRate * rateModifier))
    numChunks = int(len(readData) / chunkSize)
    readDataList = []
    for i in xrange(numChunks):
        readDataList.append( readData[i*chunkSize:(i+1)*chunkSize] )
         
    # Gather the rms of each chunk
    rmsValueList = [rootMeanSquare(vector) for vector in readDataList]
    
    # Create a list of indices to non-silence segments
    indexList = []
    for i, value in enumerate(rmsValueList):
        if value > rmsThreshold:
            print value
            indexList.append(i)
    
    # Find the longest continuous segment of noise--assume it is the utterance
    utteranceIndexList = findLongestSublist( findSequences(indexList) )
    
    # Gather the signal for the utterance indicies
    outDataList = []
    try:
        startIndex = utteranceIndexList[0]
    except IndexError:
        print "No utterance detected for %s" % (os.path.split(path)[1] + '/' + name)
        return
    endIndex = utteranceIndexList[-1]
    
    # Output warning -- no silence on the left edge (likely to have been clipped)
    if startIndex != 0:
        startIndex -= 1
    else:
        print "%s on the left edge" % (os.path.split(path)[1] + '/' + name)
        
    # Output warning -- no silence on the right edge (likely to have been clipped)
    if endIndex + 1 != len(readDataList):
        endIndex += 1
    else:
        print "%s on the right edge" % (os.path.split(path)[1] + '/' + name)
        
    for index in range(startIndex, endIndex+1):
        outDataList.append(readDataList[index])
    
    # Output data
    path = os.path.join(path, "new")    
    if not os.path.exists(path):
        os.mkdir(path)

    outputList = []
    for lst in outDataList:
        outputList.extend(lst)

    wavfile.write(os.path.join(path, name), samplingRate, numpy.int16(numpy.array(outputList)))


if __name__ == "__main__":
    
#    getWavDuration("/home/tmahrt2/Desktop/prosody/A7/03_Newman_scares_Leann.wav")
    
    rootPath = '/home/tmahrt2/Desktop/prosody_stimuli/'
    leafList = os.listdir(rootPath)
    leafList.sort()
    for fn in os.listdir(rootPath):
        
        # Skip non-wave files
        if ".wav" not in fn:
            continue
        
        fullFN = os.path.join(rootPath, fn)
        
        # Skip directories (this shouldn't be necessary...)
        if os.path.isdir(fullFN):
            continue
        
        try:
            isolateAudioString(fullFN)
        except Exception, e:
            print e
            print "Exception caught for %s" % (rootPath + '/' + fn)
            raise
        
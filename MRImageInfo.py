import os
import utils as utils
from mrjob.job import MRJob
import mrjob.protocol

#MRjob framework variables
INPUT_PROTOCOL = mrjob.protocol.RawValueProtocol
INTERNAL_PROTOCOL = mrjob.protocol.RawProtocol
OUTPUT_PROTOCOL = mrjob.protocol.RawProtocol

class MRImageInfo(MRJob):

    def mapper(self, _, line):
        profile = ""
        kdbg = ""
        imgpath = line.strip()

        # Read the image file from HDFS and write to /dev/shm
        if utils.CopyHadoopLocal('hdfs:///user/cloudera/', '/dev/shm/', imgpath):

            data = utils.RunVolatility('imageinfo', 'file:///dev/shm/'+imgpath)

            for line in data:
                yield imgpath, line.strip()

            os.remove('/dev/shm/'+imgpath)

    def reducer(self, key, values):
        for value in values:
            if value:           
                yield key, value

if __name__ == '__main__':
    MRImageInfo.run()

import sys
import os.path
import numpy as np
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from voronoi import voronoi2 as voronoi3


if __name__=='__main__':
    count = int(sys.argv[1]) if len(sys.argv)>1 else 100
    if count <= 100:
        import matplotlib.pyplot as plt
        from matplotlib.collections import LineCollection
        
    points=np.random.rand(count,2)*100  
    #points=[[-10,-10], [-10,10], [10,-10], [10,10]]
    #points=np.asarray(points, dtype=np.double)
    #print repr(points)
    now=time.time()
    lines=voronoi3(points,  (-20,-20, 120, 120)) #(-20037508.3427, -15538711.096, 20037508.3427, 15538711.096))#
    print 'voronoi took %f secs' % (time.time()-now, )
    #print lines
    if count > 100:
        sys.exit()
    plt.scatter(points[:,0], points[:,1], color="blue")
    lines = LineCollection(lines, color='red')
    plt.gca().add_collection(lines)
    #plt.axis((10,20, 47,53))
    plt.axis((-25,125, -25,125)) #(-20037508.3427,  20037508.3427, -15538711.096, 15538711.096))
    plt.show()

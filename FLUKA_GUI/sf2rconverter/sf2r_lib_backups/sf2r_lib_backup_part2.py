###-------------------------------------------------------------------
#
""" 
   --> core functionality of the smart converter service

"""
#
#  @Agnieszka Oblakowska-Mucha
#  @Tomasz Szumlak
#
###--------------------------------------------------------------------

# import section
import os, sys, getopt
from commands import getoutput
from ROOT import TH1F, TH2D, kTRUE, kRed
from ctypes import *
from itertools import count
import numpy as np

unique_cnt = count()

class sf2r_manager(object):
    # first grab the path and file name
    def __init__(self, debug = False):
        """

           __init__() - constructor
           class fields
           @__path  - path to the files produced by fluka
           @__debug - flag that can be set to printout and debugging
           @__name  - if set only this file will be converted, if no name is
                      given the manager will make a list of all files with
                      .lis extension
           @__names - a list of names of files to convert (see also __name)
           @__types - pairs of file names and types
           
        """

        self.__path = None
        self.__debug = debug
        self.__name = None
        self.__names = []
        self.__1dplot = '1DPLOT'
        self.__2dplot = '2DPLOT'
        self.__3dplot = '3DPLOT'
        self.__types = {}

        try:
            opts, args = getopt.getopt( sys.argv[1:], 'hp:d:n:', ['help', 'path=', 'debug=', 'name='])
        except getopt.GetoptError, err:
            print str(err)
            self.__help()
            sys.exit( 2 )
        if len( opts ) == 0:
            self.__help()
            sys.exit( 2 )
        for opt, arg in opts:
            if opt in ( '-h', '--help' ):
                self.__help()
            elif opt in ( '-p', '--path' ):
                self.__path = arg
                if self.__path and os.path.exists( self.__path ):
                    print ' --> Will search files to convert at: ', self.__path
                else:
                    print ' --> There is a problem with the path! Check it please.'
                    sys.exit( 2 )
            elif opt in ( '-d', '--debug' ):
                if arg:
                    print ' setting DEBUG '
                    self.__debug = True
            elif opt in ( '-n', '--name' ):
                if os.path.exists( self.__path + '/' + arg ):
                    self.__name = arg
                else:
                    print ' --> No such file exists! Check the name or path '
                    sys.exit( 2 )
            else:
                assert False, ' --> Invalid argument has been given! '
                self.__help()
                sys.exit( 2 )

        if self.__name == None:
            olist = os.listdir( self.__path )
            self.__names = [ n for n in olist if not os.path.isdir( self.__path + '/' + n ) and n.split('.')[-1] == 'lis' and n.split('.')[0][-3:] != 'sum' ]
            if self.__debug:
                print ' --> Will attempt to process the following files: '
                for name in sorted( self.__names ):
                    print name
        else:
            print ' --> Will process: ', self.__name

    def ff_type_detector(self):
        print ' --> Checking the content of the fluka files '
        command_str_2d = 'grep \'X coordinate\' '
        command_str_3d = 'grep \'R coordinate\' '
        if 0 == len( self.__names ):
            # process just one file    
            out_str = getoutput( command_str_2d  + self.__path + '/' + self.__name )
            if 0 == len( out_str ):
                out_str_3d = getoutput( command_str_3d  + self.__path + '/' + self.__name )
                if 0 == len( out_str_3d ):
                    self.__types[ self.__path + '/' + self.__name ] = self.__1dplot
                else:
                    self.__types[ self.__path + '/' + self.__name ] = self.__3dplot
            else:
                self.__types[ self.__path + '/' + self.__name ] = self.__2dplot
        else:
            # process many files
            for name in self.__names:
                out_str = getoutput( command_str_2d  + self.__path + '/' + name )
                if 0 == len( out_str ):
                    out_str_3d = getoutput( command_str_3d  + self.__path + '/' + name )
                    if 0 == len( out_str_3d ):
                        self.__types[ self.__path + '/' + name ] = self.__1dplot
                    else:
                        self.__types[ self.__path + '/' + name ] = self.__3dplot
                else:
                    self.__types[ self.__path + '/' + name ] = self.__2dplot
        for file in self.__types.keys():
            print ' --> File name: ', file, ', file type: ', self.__types[ file ]

    def __create_parsers(self):
        pfactory = ff_parser_factory( self.__types )
        return ( pfactory.ff_parser_creator() )

    def run(self):
        parsers = self.__engine_run()
        hfactory = histo_plot_factory( parsers )
        return ( hfactory.plot_creator() )

    def __engine_run(self):
        parsers = self.__create_parsers()
        return ( parsers )

    # may be useful to have getters...
    @property
    def path(self):
        return ( self.__path )

    @property
    def debug(self):
        return ( self.__debug )

    def set_debug(self, debug):
        self.__debug = debug

    @property
    def name(self):
        return ( self.__name )

    @property
    def names(self):
        return ( self.__names )

    # it is good to have some help...
    def __help(self):
        print ' ##################################################################################  '
        print ' --> You need to specify the path to repository containing files produced by fluka   '
        print '    -> use option -h or --help to print this message                                 '
        print '    -> use option -p or --path to specify the path to fluka files                    '
        print '    -> use option -n or --name to specify the name of file to be processed,          '
        print '       if none is given all .lis files will be processed                             '
        print ' ##################################################################################  '

# parser factory
class ff_parser_factory(object):
    def __init__(self, type_list):
        self.__file_types = type_list
        self.__parsers = []

    def ff_parser_creator(self):
        for file_name in self.__file_types.keys():
            f_ptr = open( file_name, 'r' )
            file_n = file_name.split('/')[-1]
            if '1DPLOT' == self.__file_types[ file_name ]:
                self.__parsers.append( ff_parser_1d( f_ptr, file_n ) )
            elif '2DPLOT' == self.__file_types[ file_name ]:
                self.__parsers.append( ff_parser_2d( f_ptr, file_n ) )
            elif '3DPLOT' == self.__file_types[ file_name ]:
                self.__parsers.append( ff_parser_3d( f_ptr, file_n ) )
        return ( self.__parsers )

# parser 1d type
class ff_parser_1d(object):
    def __init__(self, file_ptr, file_name):
        self.__header = []
        self.__data = []
        self.__f_ptr = file_ptr
        self.__file_name = file_name
        self.__header_info = { }
        self.__histogram = { }
        self.__ptype = '1DPLOT'
        self.__detect_data()
        self.__decode_header()
        self.__decode_data()
        print ' -> Decoding/parsing: ', self.__file_name

    # now check where the data begins
    def __detect_data(self):
        bchars = ['', '#']
        raw = self.__f_ptr.read().split('\n')
        for line in raw:
            line = line.split(' ')
            elements = [ ch for ch in line if ch not in bchars ]
            if len( elements ):
                if elements[0][:1].isdigit():
                    self.__data.append( elements )
                else:
                    self.__header.append( elements )
        #print ' -> header: ', self.__header 

    def __decode_header(self):
        # these corresond to the header structure, we grab the histo name and the binning
        histo_name = ( 0, 3 )
        bins = ( 1, -1 )
        self.__header_info[ 'H_NAME' ] = self.__header[ histo_name[0] ][ histo_name[1] ]
        self.__header_info[ 'BINS' ] = int( self.__header[ bins[0] ][ bins[1] ] )
        #print self.__header_info[ 'H_NAME' ], self.__header_info[ 'BINS' ]
        
    def __decode_data(self):
        # these constants pertain to the location of the data
        brange = ( 0, 0, self.__header_info[ 'BINS' ] -1, 1 )
        data = (2, 3)
        self.__histogram[ 'BINS_RANGE' ] = ( self.__data[ brange[0] ][ brange[1] ], self.__data[ brange[2] ][ brange[3] ] )
        self.__histogram[ 'TYPE' ] = self.__ptype
        data_points = []
        data_errors = []

        for line in self.__data:
            data_points.append( float( line[ data[0] ] ) )
            data_errors.append( float( line[ data[0] ] ) * ( float( line[ data[1] ] )/100. ) )
        
        self.__histogram[ 'DATA' ] = data_points
        self.__histogram[ 'ERRORS' ] = data_errors
        assert( len( self.__histogram[ 'DATA' ] ) == len( self.__histogram[ 'ERRORS' ] ) )
        #print len( self.__histogram[ 'DATA' ] )

    def get_histogram_data(self):
        return ( self.__histogram )

    def get_header_info(self):
        return ( self.__header_info )

    def get_type(self):
        return ( self.__ptype )

    def get_file_name(self):
        return ( self.__file_name )

# parser 2d type
class ff_parser_2d(object):
    def __init__(self, file_ptr, file_name):
        self.__header = []
        self.__data = []
        self.__f_ptr = file_ptr
        self.__file_name = file_name
        self.__header_info = { }
        self.__histogram = { }
        self.__ptype = '2DPLOT'
        self.__detect_data()
        self.__decode_header()
        self.__decode_data()
        print ' -> Decoding/parsing: ', self.__file_name

# now check where the data begins
    def __detect_data(self):
        bchars = ['', ' ']
        raw = self.__f_ptr.read().split('\n')
        for line in raw:
            line = line.split(' ')
            elements = [ ch for ch in line if ch not in bchars ]
            if len( elements ) > 1:
                if elements[0][:1].isdigit():
                    for el in elements:
                        self.__data.append( el )
                else:
                    self.__header.append( elements )
        #print ' --> header: ', self.__header, ' --> data: ', self.__data

    def __decode_header(self):
        # these corresond to the header structure, we grab the histo name and the binning
        histo_name = ( 0, 4 )
        bins = ( 1, 2, 3, 7 )
        xran = ( 1, 3, 5 )
        yran = ( 2, 3, 5 )
        zran = ( 3, 5 )
        self.__header_info[ 'H_NAME' ] = self.__header[ histo_name[0] ][ histo_name[1] ]
        self.__header_info[ 'XBINS' ] = int( self.__header[ bins[0] ][ bins[3] ] )
        self.__header_info[ 'YBINS' ] = int( self.__header[ bins[1] ][ bins[3] ] )
        self.__header_info[ 'ZBINS' ] = int( self.__header[ bins[2] ][ bins[3] ] )
        xl = float( self.__header[ xran[0] ][ xran[1] ] )
        xh = float( self.__header[ xran[0] ][ xran[2] ] )
        self.__header_info[ 'XRAN' ] = ( xl, xh )
        yl = float( self.__header[ yran[0] ][ yran[1] ] )
        yh = float( self.__header[ yran[0] ][ yran[2] ] )
        self.__header_info[ 'YRAN' ] = ( yl, yh )
        zl = float( self.__header[ zran[0] ][ zran[0] ] )
        zh = float( self.__header[ zran[0] ][ zran[1] ] )
        self.__header_info[ 'ZRAN' ] = ( zl, zh )

        #print self.__header_info[ 'H_NAME' ], self.__header_info[ 'XBINS' ]
        #print self.__header_info[ 'YBINS' ], self.__header_info[ 'ZBINS' ]

    def __decode_data(self):
        # these constants pertain to the location of the data
        self.__histogram[ 'TYPE' ] = self.__ptype
        data_points = []

        for el in self.__data:
            data_points.append( float( el ) )
            
        self.__histogram[ 'DATA' ] = data_points
        #print len( self.__histogram[ 'DATA' ] )

    def get_header_info(self):
        return ( self.__header_info )

    def get_histogram_data(self):
        return ( self.__histogram )

    def get_type(self):
        return ( self.__ptype )

    def get_file_name(self):
        return ( self.__file_name )


# parser 3d type
class ff_parser_3d(object):
    def __init__(self, file_ptr, file_name):
        self.__header = []
        self.__data = []
        self.__f_ptr = file_ptr
        self.__file_name = file_name
        self.__header_info = { }
        self.__histogram = { }
        self.__ptype = '3DPLOT'
        self.__detect_data()
        self.__decode_header()
        self.__decode_data()
        print ' -> Decoding/parsing: ', self.__file_name

# now check where the data begins
    def __detect_data(self):
        bchars = ['', ' ']
        raw = self.__f_ptr.read().split('\n')
        for line in raw:
            line = line.split(' ')
            elements = [ ch for ch in line if ch not in bchars ]
            if len( elements ) > 1:
                if elements[0][:1].isdigit():
                    for el in elements:
                        self.__data.append( el )
                else:
                    self.__header.append( elements )
        #print ' --> header: ', self.__header, ' --> data: ', self.__data

    def __decode_header(self):
        # these corresond to the header structure, we grab the histo name and the binning
        histo_name = ( 0, 4 )
        bins = ( 1, 2, 3, 7 )
        rran = ( 1, 3, 5 )
        pran = ( 2, 3, 5 )
        zran = ( 3, 5 )
        self.__header_info[ 'H_NAME' ] = self.__header[ histo_name[0] ][ histo_name[1] ]
        self.__header_info[ 'RBINS' ] = int( self.__header[ bins[0] ][ bins[3] ] )
        self.__header_info[ 'PBINS' ] = int( self.__header[ bins[1] ][ bins[3] ] )
        self.__header_info[ 'ZBINS' ] = int( self.__header[ bins[2] ][ bins[3] ] )
        rl = float( self.__header[ rran[0] ][ rran[1] ] )
        rh = float( self.__header[ rran[0] ][ rran[2] ] )
        self.__header_info[ 'RRAN' ] = ( rl, rh )
        pl = float( self.__header[ pran[0] ][ pran[1] ] )
        ph = float( self.__header[ pran[0] ][ pran[2] ] )
        self.__header_info[ 'PRAN' ] = ( pl, ph )
        zl = float( self.__header[ zran[0] ][ zran[0] ] )
        zh = float( self.__header[ zran[0] ][ zran[1] ] )
        self.__header_info[ 'ZRAN' ] = ( zl, zh )

        #print self.__header_info[ 'H_NAME' ], self.__header_info[ 'RBINS' ]
        #print self.__header_info[ 'PBINS' ], self.__header_info[ 'ZBINS' ]

    def __decode_data(self):
        # these constants pertain to the location of the data
        self.__histogram[ 'TYPE' ] = self.__ptype
        data_points = []
        error_points = []
        for el in xrange(len(self.__data)/2):
            data_points.append( float( self.__data[el] ) )
        for err in xrange(len(self.__data)/2,len(self.__data)):
            error_points.append( float( self.__data[err] ) )
#SO HERE I MAKE THE SUPERPOSITION OF 2 AND 3 PART OF GRAPH
#Commented for part 1 and 4 with !!! at the begining
#What should we do with x%2==1 bins of phi???
        if self.__header_info[ 'PBINS' ]>3:
            fine_data_indx=len(data_points)/4
            #!!!second_part_of_fine_data=len(data_points)-fine_data_indx
            #!!!for x in range(fine_data_indx):
                #!!!superpos_el=(float(data_points[x]+data_points[second_part_of_fine_data+x])/2)
            centre_of_fine_data=len(data_points)-(2*fine_data_indx)
            for x in xrange(fine_data_indx,centre_of_fine_data):
                superpos_el=float(data_points[x]+data_points[centre_of_fine_data+x%fine_data_indx])/2
		#print superpos_el
                data_points.append(superpos_el)
#FOR ERRORS SHOULD BE DONE. FANCIER THAN AVERAGE???        
        self.__histogram[ 'DATA' ] = data_points
        self.__histogram[ 'ERRORS' ] = error_points
        #print len( self.__histogram[ 'DATA' ] )

    def get_header_info(self):
        return ( self.__header_info )

    def get_histogram_data(self):
        return ( self.__histogram )

    def get_type(self):
        return ( self.__ptype )

    def get_file_name(self):
        return ( self.__file_name )


# histo factory
class histo_plot_factory(object):
    def __init__(self, parsers):
        self.__parsers = parsers 
        self.__plots = []

    def plot_creator(self):
        for parser in self.__parsers:
            if '1DPLOT' == parser.get_type():
                self.__plots.append( plot_1d( parser ) )
            elif '2DPLOT' == parser.get_type():
                self.__plots.append( plot_2d( parser ) )
            elif '3DPLOT' == parser.get_type():
                self.__plots.append( plot_3d( parser ) )
        return ( self.__plots )

# plot 1d
class plot_1d(object):
    def __init__(self, parser):
        self.__parser = parser
        self.__histo = None
        self.__plot_1d()
        self.__type = '1DPLOT'
        print ' -> Plotting/writing: ', self.__parser.get_file_name()

    def __plot_1d(self):
        global unique_cnt
        uid = next(unique_cnt)
        header = self.__parser.get_header_info()
        hdata = self.__parser.get_histogram_data()
        name = header[ 'H_NAME' ] + str( uid )
        bins = header[ 'BINS' ]
        xlow = hdata[ 'BINS_RANGE' ][0]
        xup = hdata[ 'BINS_RANGE' ][1]
        self.__histo = TH1F(name, name, int(bins), float(xlow), float(xup))
        for indx, data_point in enumerate( hdata[ 'DATA' ] ):
            self.__histo.SetBinContent( indx + 1, data_point )
        for indx, error in enumerate( hdata[ 'ERRORS' ] ):
            self.__histo.SetBinError( indx + 1, error )
        min_val = min( hdata[ 'DATA' ] )
        max_val = max( hdata[ 'DATA' ] )
        self.__histo.SetMarkerStyle( 20 )
        self.__histo.SetMarkerSize( 0.6 )

    def set_histo_data(self, hdata):
        self.__hdata = hdata

    def get_histo(self):
        return ( self.__histo )

    def get_type(self):
        return ( self.__type )

# plot 2d
class plot_2d(object):
    def __init__(self, parser):
        self.__parser = parser
        self.__histo = None
        self.__plot_2d()
        self.__type = '2DPLOT'
        print ' -> Plotting/writing: ', self.__parser.get_file_name()

    def __plot_2d(self):
        global unique_cnt
        uid = next(unique_cnt)
        header = self.__parser.get_header_info()
        hdata = self.__parser.get_histogram_data()[ 'DATA' ]
        name = header[ 'H_NAME' ] + ' ' + str( uid )
        name = name[1:]
        nybins = header[ 'YBINS' ]
        nzbins = header[ 'ZBINS' ]
        yl = header[ 'YRAN' ][0]
        yu = header[ 'YRAN' ][1]
        zl = header[ 'ZRAN' ][0]
        zu = header[ 'ZRAN' ][1]
        self.__histo = TH2D(name, name, int( nzbins ) , float( zl ), float( zu ), int( nybins ), float( yl ),float(  yu ))
        self.__histo.SetXTitle("Z [cm]")
        self.__histo.GetXaxis().CenterTitle(kTRUE)
        self.__histo.GetXaxis().SetTitleOffset(1.1)
        self.__histo.GetXaxis().SetTitleSize(0.04)
        self.__histo.GetXaxis().SetLabelSize(0.03)
        self.__histo.GetXaxis().SetTickLength(0.02)
        self.__histo.GetXaxis().SetNdivisions(20510)
        self.__histo.SetYTitle("Y [cm]")
        self.__histo.GetYaxis().CenterTitle(kTRUE)
        self.__histo.GetYaxis().SetTitleOffset(1.2)
        self.__histo.GetYaxis().SetTitleSize(0.04)
        self.__histo.GetYaxis().SetLabelSize(0.03)
        self.__histo.GetYaxis().SetTickLength(0.02)
        self.__histo.GetYaxis().SetNdivisions(20510)
        self.__histo.SetLineColor(kRed);
        self.__histo.SetMinimum(1e-9);
        self.__histo.GetZaxis().SetTitle("a.u.");

        nxbins = header[ 'XBINS' ]
        ResX = ( header[ 'XRAN' ][1] - header[ 'XRAN' ][0] ) / nxbins
        ResY = ( yu - yl ) / nybins
        ResZ = ( zu - zl ) / nzbins
        FirstX = header[ 'XRAN' ][0] + ResX / 2.
        FirstY = yl + ResY / 2.
        FirstZ = zl + ResZ / 2.
        N = nxbins * nybins * nzbins
        zPos = [ None ] * N
        xPos = [ None ] * N
        yPos = [ None ] * N
        # -> fill the histo now!
        pos_cnt = 0
        for zentry in range( nzbins ):
            zPos[zentry] = FirstZ + float(zentry) * ResZ;
            for yentry in range( nybins ):
                for xentry in range( nxbins ):
                    data_point = hdata[ pos_cnt ]
                    xPos[xentry] = FirstX + float( xentry ) * ResX
                    yPos[yentry] = FirstY + float( yentry ) * ResY
                    self.__histo.Fill( zPos[zentry], yPos[yentry], data_point)
                    pos_cnt += 1

    def get_histo(self):
        return ( self.__histo )

    def get_type(self):
        return ( self.__type )
        

# plot 3d
class plot_3d(object):
    def __init__(self, parser):
        self.__parser = parser
        self.__histo = None
        self.__plot_3d()
        self.__type = '3DPLOT'
        print ' -> Plotting/writing: ', self.__parser.get_file_name()

    def __plot_3d(self):
        global unique_cnt
        definite_integral=0.
        uid = next(unique_cnt)
        header = self.__parser.get_header_info()
        hdata = self.__parser.get_histogram_data()[ 'DATA' ]
        name = header[ 'H_NAME' ] + ' ' + str( uid )
        name = name[1:]
        nrbins = header[ 'RBINS' ]
        npbins = header[ 'PBINS' ]
        nzbins = header[ 'ZBINS' ]
        rl = header[ 'RRAN' ][0]
        ru = header[ 'RRAN' ][1]
        pl = header[ 'PRAN' ][0]
        pu = header[ 'PRAN' ][1]
        zl = header[ 'ZRAN' ][0]
        zu = header[ 'ZRAN' ][1]
        ## ------   TH2D::TH2D(const char* name, const char* title, int nbinsx, double xlow, double xup, int nbinsy, double ylow, double yup)
        self.__histo = TH2D(name, name, int( nrbins * npbins ) , float( zl ), float( zu ), int( nrbins * npbins ), float( pl ),float(  pu ))
        self.__histo.SetXTitle("X [cm]")
        self.__histo.GetXaxis().CenterTitle(kTRUE)
        self.__histo.GetXaxis().SetTitleOffset(1.1)
        self.__histo.GetXaxis().SetTitleSize(0.04)
        self.__histo.GetXaxis().SetLabelSize(0.03)
        self.__histo.GetXaxis().SetTickLength(0.02)
        self.__histo.GetXaxis().SetNdivisions(20510)
        self.__histo.SetYTitle("Y [cm]")
        self.__histo.GetYaxis().CenterTitle(kTRUE)
        self.__histo.GetYaxis().SetTitleOffset(1.2)
        self.__histo.GetYaxis().SetTitleSize(0.04)
        self.__histo.GetYaxis().SetLabelSize(0.03)
        self.__histo.GetYaxis().SetTickLength(0.02)
        self.__histo.GetYaxis().SetNdivisions(20510)
        self.__histo.SetLineColor(kRed);
        #self.__histo.SetMinimum(1e-9);
        self.__histo.GetZaxis().SetTitle("Z [cm]");

        ResR = ( ru - rl ) / nrbins
        ResP = ( pu - pl ) / npbins
        ResZ = ( zu - zl ) / nzbins
        FirstR = rl + ResR / 2.
        FirstP = pl + ResP / 2.
        FirstZ = zl + ResZ / 2.
        N = nrbins * npbins * nzbins
        rPos = [ None ] * N
        pPos = [ None ] * N
        zPos = [ None ] * N
        # -> fill the histo now!
        pos_cnt = 0
         
        
        uid = next(unique_cnt)
        header = self.__parser.get_header_info()
        hdata = self.__parser.get_histogram_data()
        name = header[ 'H_NAME' ] + str( uid )
        bins = header[ 'RBINS' ]
        
        self.__histo = [ None ]* (npbins+1)
        #ddebg = [[],[],[],[] ]
        #edebg = [ [],[],[],[]]
        
        for i in range(npbins):
            self.__histo[i] = TH1F(name+' phi='+str(FirstP+i*ResP), name+' phi='+str(FirstP+i*ResP), int(nrbins), float(rl), float(ru))
#SUPERPOSITION COMING RIGHT NOW!!!
        self.__histo[npbins] = TH1F(name+' Superposition', name+' Superposition', int(nrbins), float(rl), float(ru))
#AND ENDS RIGHT HERE            
        for indx, data_point in enumerate( hdata[ 'DATA' ] ):
            self.__histo[int(indx/nrbins)].SetBinContent( indx%nrbins +1, data_point )
            if indx%nrbins==0 and indx!=0:
                print "Definite integral for %d graph = %.4f" %(int(indx/nrbins),definite_integral)
                definite_integral=data_point
            else:
                definite_integral+=data_point
        print "Definite integral for 5 graph = %.4f" %definite_integral
            #ddebg[int(indx/100)].append(data_point)
            
        #for indx, error in enumerate( hdata[ 'ERRORS' ] ):
            #self.__histo[int(indx/100)].SetBinError( indx%100 + 1, error )
            #edebg[int(indx/100)].append(error)

        #print len(ddebg[0]), len(ddebg[1]), len(ddebg[2]), len(ddebg[3])
        #print len(edebg[0]), len(edebg[1]), len(edebg[2]), len(edebg[3]),

        min_val = min( hdata[ 'DATA' ] )
        max_val = max( hdata[ 'DATA' ] )
        
        for l in range(npbins):
            self.__histo[l].SetMarkerStyle( 20 )
            self.__histo[l].SetMarkerSize( 0.6 )



    def get_histo(self):
        return ( self.__histo )

    def get_type(self):
        return ( self.__type )
        

# state service
class state_svc():
    def __init__(self):
        self.__histo_cnt = 0
   

#!/usr/bin/env python

"""
Module for parsing MCNP output data. MCNP is a general-purpose Monte Carlo
N-Particle code developed at Los Alamos National Laboratory that can be used for
neutron, photon, electron, or coupled neutron/photon/electron transport. Further
information on MCNP can be obtained from http://mcnp-green.lanl.gov/

Mctal and Runtpe classes still need work. Also should add Meshtal and Outp
classes.

"""

import collections
import string
import struct
import math 
import os
import linecache
import tables

import numpy as np

from pyne.material import Material
from pyne.material import MultiMaterial
from pyne import nucname
from binaryreader import _BinaryReader, _FortranRecord


class Mctal(object):
    def __init__(self):
        pass

    def read(self, filename):
        """Parses a 'mctal' tally output file from MCNP. Currently this
        only supports reading the kcode data- the remaining tally data
        will not be read.
        """

        # open file
        self.f = open(filename, 'r')

        # get code name, version, date/time, etc
        words = self.f.readline().split()
        self.codeName = words[0]
        self.codeVersion = words[1]
        self.codeDate = words[2]
        self.codeTime = words[3]
        self.n_dump = words[4]
        self.n_histories = int(words[5])
        self.n_prn       = int(words[6])

        # comment line of input file
        self.comment = self.f.readline().strip()

        # read tally line
        words = self.f.readline().split()
        self.n_tallies = words[1]
        if len(words) > 2:
            # perturbation tallies present
            pass

        # read tally numbers
        tally_nums = [int(i) for i in self.f.readline().split()]

        # read tallies
        for i_tal in tally_nums:
            pass

        # read kcode information
        words = self.f.readline().split()
        self.n_cycles = int(words[1])
        self.n_inactive = int(words[2])
        vars_per_cycle = int(words[3])

        self.k_col = []
        self.k_abs = []
        self.k_path = []
        self.prompt_life_col = []
        self.prompt_life_path = []
        self.avg_k_col = []
        self.avg_k_abs = []
        self.avg_k_path = []
        self.avg_k_combined = []
        self.avg_k_combined_active = []
        self.prompt_life_combined = []
        self.cycle_histories = []
        self.avg_k_combined_FOM = []

        for cycle in range(self.n_cycles):
            # read keff and prompt neutron lifetimes
            if vars_per_cycle == 0 or vars_per_cycle == 5:
                values = [float(i) for i in get_words(self.f, lines = 1)]
            elif vars_per_cycle == 19:
                values = [float(i) for i in get_words(self.f, lines = 4)]
            
            self.k_col.append(values[0])
            self.k_abs.append(values[1])
            self.k_path.append(values[2])
            self.prompt_life_col.append(values[3])
            self.prompt_life_path.append(values[4])

            if vars_per_cycle <= 5:
                continue

            avg, stdev = (values[5],values[6])
            self.avg_k_col.append((avg,stdev))
            avg, stdev = (values[7],values[8])
            self.avg_k_abs.append((avg,stdev))
            avg, stdev = (values[9],values[10])
            self.avg_k_path.append((avg,stdev))
            avg, stdev = (values[11],values[12])
            self.avg_k_combined.append((avg,stdev))
            avg, stdev = (values[13],values[14])
            self.avg_k_combined_active.append((avg,stdev))
            avg, stdev = (values[15],values[16])
            self.prompt_life_combined.append((avg,stdev))
            self.cycle_histories.append(values[17])
            self.avg_k_combined_FOM.append(values[18])
            
def get_words(f, lines = 1):
    words = []
    for i in range(lines):
        local_words = f.readline().split()
        words += local_words
    return words

class SourceSurf(object):
    def __init__(self):
        pass

class TrackData(object):
    def __init__(self):
        pass

class SurfSrc(_BinaryReader):

    def __init__(self, filename, mode="rb"):
        super(SurfSrc, self).__init__(filename,mode)

    def __str__(self):
        return self.print_header()

    def print_header(self):
        headerString  = "Code: {0} (version: {1}) [{2}]\n".format(self.kod, self.ver, self.loddat)
        headerString += "Problem info: ({0}) {1}\n{2}\n".format(self.idtm, self.probid, self.aid)
        headerString += "Showing dump #{0}\n".format(self.knod)
        headerString += "{0} histories, {1} tracks, {2} record size, {3} surfaces, {4} histories\n".format(self.np1, self.nrss, self.ncrd, self.njsw, self.niss)
        headerString += "{0} cells, source particle: {1}, macrobody facet flag: {2}\n".format(self.niwr, self.mipts, self.kjaq)
        for i in self.surflist:
            headerString += "Surface {0}: facet {1}, type {2} with {3} parameters: (".format(i.id, i.facetId, i.type, i.numParams)
            if i.numParams > 1:
                for j in i.surfParams:
                    headerString += " {0}".format(j)
            else:
                headerString += " {0}".format(i.surfParams)
            headerString += ")\n"
        headerString += "Summary Table: " + str(self.summaryTable)

        return headerString

    def print_tracklist(self):
        trackData = "Track Data\n"
  #                       1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890
        trackData +=     "       nps   BITARRAY        WGT        ERG        TME             X             Y             Z          U          V     COSINE  |       W\n"
        for j in self.tracklist:
            trackData += "%10d %10g %10.5g %10.5g %10.5g %13.5e %13.5e %13.5e %10.5f %10.5f %10.5f  | %10.5f " % (j.nps, j.bitarray, j.wgt, j.erg, j.tme, j.x, j.y, j.z, j.u, j.v, j.cs, j.w) + "\n"

        return trackData

    def compare(self,other):
        """ """

        if other.kod != self.kod:
            print "kod does not match"
            return False
        if other.ver != self.ver:
            print "ver does not match"
            return False
        if other.loddat != self.loddat:
            print "loddat does not match"
            return False

        if other.ncrd != self.ncrd:
            print "ncrd does not match"
            return False
        if other.njsw != self.njsw:
            print "njsw does not match"
            return False

        if other.niwr  != self.niwr:
            print "niwr does not match"
            return False
        if other.mipts != self.mipts:
            print "mipts does not match"
            return False
        if other.kjaq  != self.kjaq:
            print "kjaq does not match"
            return False

        for surf in range(len(self.surflist)):
            if other.surflist[surf].id         != self.surflist[surf].id:
                print "surf " + str(surf) + " ID doesn't match"
                return False
            if other.surflist[surf].facetId    != self.surflist[surf].facetId:
                print "surf " + str(surf) + " facetId doesn't match"
                return False
            if other.surflist[surf].type       != self.surflist[surf].type:
                print "surf " + str(surf) + " type doesn't match"
                return False
            if other.surflist[surf].numParams  != self.surflist[surf].numParams:
                print "surf " + str(surf) + " numParams doesn't match"
                return False
            if other.surflist[surf].surfParams != self.surflist[surf].surfParams:
                print "surf " + str(surf) + " surfParams doesn't match"
                return False

        return True

    def read_header(self):
        """Read in the header block data

        This block comprises 4 fortran records which we refer to as:
        header, table1, table2, summary
        """
        # read header record
        header = self.get_fortran_record()

        # interpret header 
        self.kod    = header.get_string(8)[0]  # code identifier
        self.ver    = header.get_string(5)[0]  # code version identifier
        self.loddat = header.get_string(8)[0]  # code version date
        self.idtm   = header.get_string(19)[0] # current date and time
        self.probid = header.get_string(19)[0] # problem identification string
        self.aid    = header.get_string(80)[0] # title card of initial run
        self.knod   = header.get_int()[0]      # dump number

        # read table 1 record; various counts and sizes
        tablelengths = self.get_fortran_record()

        # interpret table lengths
        self.np1  = tablelengths.get_long()[0]  # number of histories used to generate source
        self.nrss = tablelengths.get_long()[0]  # number of tracks written to surface source
        self.ncrd = tablelengths.get_int()[0]  # number of values in surface source record
                                               # 6 for a spherical source
                                               # 11 otherwise
        self.njsw = tablelengths.get_int()[0]   # number of surfaces
        self.niss = tablelengths.get_long()[0]  # number of histories written to surface source

        if self.np1 < 0:
            # read table 2 record; more size info
            tablelengths = self.get_fortran_record()

            self.niwr  = tablelengths.get_int()[0]  # number of cells in surface source card
            self.mipts = tablelengths.get_int()[0]  # source particle type
            self.kjaq  = tablelengths.get_int()[0]  # macrobody facet flag
            self.table2extra=[]
            while tablelengths.numBytes > tablelengths.pos:
                self.table2extra += tablelengths.get_int()
            # print "np1 is ", self.np1
        else:
            # print "np1 is ", self.np1
            pass
        
        self.orignp1 = self.np1
        
        self.np1 = abs(self.np1)

        # get info for each surface
        self.surflist = []
        for j in range(self.njsw):
            # read next surface info record
            self.surfaceinfo = self.get_fortran_record()
            
            surfinfo = SourceSurf()
            surfinfo.id = self.surfaceinfo.get_int()            # surface ID
            if self.kjaq == 1:
                surfinfo.facetId = self.surfaceinfo.get_int()   # facet ID
            else:
                surfinfo.facetId = -1                           # dummy facet ID

            surfinfo.type = self.surfaceinfo.get_int()                 # surface type
            surfinfo.numParams = self.surfaceinfo.get_int()[0]         # number of surface parameters
            surfinfo.surfParams = self.surfaceinfo.get_double(surfinfo.numParams)

            self.surflist.append(surfinfo)                  

        # We read any extra records as determined by njsw+niwr...
        #  No known case of their actual utility is known currently
        for j in range(self.njsw,self.njsw+self.niwr):
            self.get_fortran_record()
            print "Extra info in header not handled:", j

        # read summary table record
        summaryInfo = self.get_fortran_record()
        self.summaryTable = summaryInfo.get_int((2+4*self.mipts)*(self.njsw+self.niwr)+1)
        self.summaryExtra=[]
        while summaryInfo.numBytes > summaryInfo.pos:
            self.summaryExtra += summaryInfo.get_int()
        

    def read_tracklist(self):
        """
        Reads in track records for individual particles.
        """
        self.tracklist = []
        for j in range(self.nrss):
            trackInfo = self.get_fortran_record()
            trackData = TrackData()
            trackData.record   = trackInfo.get_double(self.ncrd)
            trackData.nps      = trackData.record[0]
            trackData.bitarray = trackData.record[1]
            trackData.wgt      = trackData.record[2]
            trackData.erg      = trackData.record[3]
            trackData.tme      = trackData.record[4]
            trackData.x        = trackData.record[5]
            trackData.y        = trackData.record[6]
            trackData.z        = trackData.record[7]
            trackData.u        = trackData.record[8]
            trackData.v        = trackData.record[9]
            trackData.cs       = trackData.record[10]
            trackData.w        = math.copysign(math.sqrt(1 - trackData.u*trackData.u - trackData.v*trackData.v),trackData.bitarray)
            # trackData.bitarray = abs(trackData.bitarray)
            
            self.tracklist.append(trackData)       
        return


    def put_header(self):
        """
        Write the header part of the header
        to the surface source file
        """
        rec = [self.kod, self.ver, self.loddat, self.idtm, self.probid, self.aid]
        newrecord = _FortranRecord("".join(rec), len("".join(rec)))
        newrecord.put_int([self.knod])
        self.put_fortran_record(newrecord)
        return
    
    
    def put_table_1(self):
        """
        Write the table1 part of the header
        to the surface source file
        """
        newrecord = _FortranRecord("", 0)
        newrecord.put_long( [self.np1])
        newrecord.put_long( [self.nrss])
        newrecord.put_int(  [self.ncrd])
        newrecord.put_int(  [self.njsw])
        newrecord.put_long( [self.niss])
        self.put_fortran_record(newrecord)
        return
    
    
    def put_table_2(self):
        """
        Write the table2 part of the header
        to the surface source file
        """
        newrecord = _FortranRecord("", 0)
        newrecord.put_int( [self.niwr ])
        newrecord.put_int( [self.mipts])
        newrecord.put_int( [self.kjaq ])
        newrecord.put_int( self.table2extra)
        self.put_fortran_record(newrecord)
        return


    def put_surface_info(self):
        """
        Write the record for each surface
        to the surface source file
        """

        for cnt, s in enumerate(self.surflist):
            newrecord = _FortranRecord("",0)
            newrecord.put_int(s.id)
            if self.kjaq == 1:
                newrecord.put_int(s.facetId) # don't add a 'dummy facet ID'
            # else no macrobody flag byte in the record

            newrecord.put_int(s.type)
            newrecord.put_int(s.numParams)
            newrecord.put_double(s.surfParams)
            
            self.put_fortran_record(newrecord)
        return
        
        
    def put_summary(self):
        """
        Write the summary part of the header
        to the surface source file
        """
        newrecord = _FortranRecord("", 0)
        newrecord.put_int( list(self.summaryTable) )
        newrecord.put_int( list(self.summaryExtra) )
        #newrecord.put_int( [self.summaryTable])
        #newrecord.put_int( [self.summaryExtra])
        self.put_fortran_record(newrecord)
        return


class Srctp(_BinaryReader):
    """This class stores source site data from a 'srctp' file written by
    MCNP. The source sites are stored in the 'fso' array in MCNP.
    """

    def __init__(self, filename):
        super(Srctp, self).__init__(filename)

    def read(self):
        # read header block
        header = self.get_fortran_record()

        # interpret header block
        k = header.get_int() # unique code (947830)
        self.loc_next = header.get_int() # location of next site in FSO array (ixak)
        self.n_run = header.get_int() # source particles yet to be run (nsa)
        self.loc_store = header.get_int() # where to store next source neutron (ist)
        self.n_source = header.get_int() # number of source points in fso (mrl)

        # read source site array
        fso = self.get_fortran_record()
        
        self.sites = []
        for i in range(self.n_source):
            vals = fso.get_double(11)

            site = SourceSite()
            site.x = vals[0]
            site.y = vals[1]
            site.z = vals[2]
            site.E = vals[3]

            self.sites.append(site)

    def remainingSites(self):
        index = self.loc_next - 1
        if (self.loc_next + self.n_run) >= self.n_source:
            return (self.sites[index:] + 
                    self.sites[:self.n_run - (self.n_source - index)])
        else:
            return self.sites[index : index + self.n_run]

    def __repr__(self):
        return "<Srctp: {0}>".format(self.f.name)


class SourceSite(object):
    
    def __init__(self):
        pass

    def __repr__(self):
        return "<SourceSite: ({0.x},{0.y},{0.z})>".format(self)


class Runtpe(_BinaryReader):

    def __init__(self, filename):
        super(Runtpe, self).__init__(filename)

    def read(self, filename):
        # read identification block
        header = self.get_fortran_record()

        # parse identification block
        self.codeName = header.get_string(8)
        self.codeVersion = header.get_string(5)
        self.codeDate = header.get_string(8)
        header.get_string(19) # machine designator, date and time
        self.chargeCode = header.get_string(10)
        self.problemID = header.get_string(19)
        self.problemIDsurf = header.get_string(19)
        self.title = header.get_string(80)
        header.pos += 3*6*11 # skip user file characteristics
        self.n_tables = header.get_int()

        # read cross-section tables
        self.tables = []
        for i in range(self.n_tables):
            self.tables.append(self.get_fortran_record())
            

    def __repr__(self):
        return "<Runtpe: {0}>".format(self.f.name)


class Xsdir(object):

    def __init__(self, filename):
        self.f = open(filename, 'r')
        self.filename = os.path.abspath(filename)
        self.directory = os.path.dirname(filename)
        self.awr = {}
        self.tables = []

        self.read()

    def read(self):
        # Go to beginning of file
        self.f.seek(0)

        # Read first section (DATAPATH)
        line = self.f.readline()
        words = line.split()
        if words:
            if words[0].lower().startswith('datapath'):
                index = line.index('=')
                self.datapath = line[index+1:].strip()

        # Read second section
        line = self.f.readline()
        words = line.split()
        assert len(words) == 3
        assert words[0].lower() == 'atomic'
        assert words[1].lower() == 'weight'
        assert words[2].lower() == 'ratios'

        while True:
            line = self.f.readline()
            words = line.split()

            # Check for end of second section
            if len(words) % 2 != 0 or words[0] == 'directory':
                break
            
            for zaid, awr in zip(words[::2], words[1::2]):
                self.awr[zaid] = awr

        # Read third section
        while words[0] != 'directory':
            words = self.f.readline().split()
            
        while True:
            words = self.f.readline().split()
            if not words:
                break

            # Handle continuation lines
            while words[-1] == '+':
                extraWords = self.f.readline().split()
                words = words + extraWords
            assert len(words) >= 7

            # Create XsdirTable object and add to line
            table = XsdirTable()
            self.tables.append(table)
            
            # All tables have at least 7 attributes
            table.name = words[0]
            table.awr = float(words[1])
            table.filename = words[2]
            table.access = words[3]
            table.filetype = int(words[4])
            table.address = int(words[5])
            table.tablelength = int(words[6])

            if len(words) > 7:
                table.recordlength = int(words[7])
            if len(words) > 8:
                table.entries = int(words[8])
            if len(words) > 9:
                table.temperature = float(words[9])
            if len(words) > 10:
                table.ptable = (words[10] == 'ptable')

    def find_table(self, name):
        tables = []
        for table in self:
            if name in table.name:
                tables.append(table)
        return tables

    def to_xsdata(self, filename):
        xsdata = open(filename, 'w')
        for table in self.tables:
            if table.serpent_type == 1:
                xsdata.write(table.to_serpent() + '\n')
        xsdata.close()

    def __iter__(self):
        for table in self.tables:
            yield table

class XsdirTable(object):

    def __init__(self):
        self.name = None
        self.awr = None
        self.filename = None
        self.access = None
        self.filetype = None
        self.address = None
        self.tablelength = None
        self.recordlength = None
        self.entries = None
        self.temperature = None
        self.ptable = False

    @property
    def alias(self):
        return self.name

    @property
    def serpent_type(self):
        if self.name.endswith('c'):
            return 1
        elif self.name.endswith('y'):
            return 2
        elif self.name.endswith('t'):
            return 3
        else:
            return None

    @property
    def metastable(self):
        # Only valid for neutron cross-sections
        if not self.name.endswith('c'):
            return

        # Handle special case of Am-242 and Am-242m
        if self.zaid == '95242':
            return 1
        elif self.zaid == '95642':
            return 0

        # All other cases
        A = int(self.zaid) % 1000
        if A > 600:
            return 1
        else:
            return 0

    @property
    def zaid(self):
        return self.name[:self.name.find('.')]

    def to_serpent(self, directory=''):
        # Adjust directory
        if directory:
            if not directory.endswith('/'):
                directory = directory.strip() + '/'

        return "{0} {0} {1} {2} {3} {4} {5} {6} {7}".format(
            self.name, self.serpent_type, self.zaid, 1 if self.metastable else 0,
            self.awr, self.temperature/8.6173423e-11, self.filetype - 1,
            directory + self.filename)

    def __repr__(self):
        return "<XsDirTable: {0}>".format(self.name)


class PtracEvent(tables.IsDescription):
    """This class holds one Ptrac event and serves as a table definition
    for saving Ptrac data to a HDF5 file.
    """
    event_type = tables.Int32Col()
    node    = tables.Float32Col()
    nsr     = tables.Float32Col()
    nsf     = tables.Float32Col()
    nxs     = tables.Float32Col()
    ntyn    = tables.Float32Col()
    ipt     = tables.Float32Col()
    ncl     = tables.Float32Col()
    mat     = tables.Float32Col()
    ncp     = tables.Float32Col()
    xxx     = tables.Float32Col()
    yyy     = tables.Float32Col()
    zzz     = tables.Float32Col()
    uuu     = tables.Float32Col()
    vvv     = tables.Float32Col()
    www     = tables.Float32Col()
    erg     = tables.Float32Col()
    wgt     = tables.Float32Col()
    tme     = tables.Float32Col()


class PtracReader(object):
    """Class to read _binary_ PTRAC files generated by MCNP.
    """

    def __init__(self, filename):
        """Construct a new Ptrac reader for a given filename, determine the
        number format and read the file's headers.
        """
        self.variable_mappings = {
            1: "nps",
            3: "ncl",
            4: "nsf", # surface id
            8: "node",
            9: "nsr",
            10: "nxs",
            11: "ntyn",
            12: "nsf",
            16: "ipt",
            17: "ncl",
            18: "mat",
            19: "ncp",
            20: "xxx", # position x
            21: "yyy", # position y
            22: "zzz", # position z
            23: "uuu", # cos(x-direction)
            24: "vvv", # cos(y-direction)
            25: "www", # cos(z-direction)
            26: "erg", # energy
            27: "wgt", # weight
            28: "tme"
        }

        self.eightbytes = False
    
        self.f = open(filename, 'rb')
        self.determine_endianness()
        self.read_headers()
        self.read_variable_ids()
        
        self.next_event = 0
    
    def __del__(self):
        """Destructor. The only thing to do is close the Ptrac file.
        """
        self.f.close()
        
    def determine_endianness(self):
        """Determine the number format (endianness) used in the Ptrac file.
        For this, the file's first entry is used. It is always minus one
        and has a length of 4 bytes."""
        
        # read and unpack first 4 bytes
        b = self.f.read(4)
        should_be_4 = struct.unpack('<i', b)[0]
        if should_be_4 == 4:
            self.endianness = '<'
        else:
            self.endianness = '>'
        
        # discard the next 8 bytes (the value -1 und another 4)
        self.f.read(8)

    def read_next(self, format, number=1, auto=False, raw_format=False):
        """Helper method for reading records from the Ptrac file.
        All binary records consist of the record content's length in bytes,
        the content itself and then the length again.
        format can be one of the struct module's format characters (i.e. i
        for an int, f for a float, s for a string).
        The length of the record can either be hard-coded by setting the
        number parameter (e.g. to read 10 floats) or determined automatically
        by setting auto=True.
        Setting the parameter raw_format to True means that the format string
        will not be expanded by number, but will be used directly.
        """

        if self.eightbytes and (not raw_format) and format == 'f':
            format = 'd'
        if self.eightbytes and (not raw_format) and format == 'i':
            format = 'q'
    
        # how long is one field of the read values
        format_length = 1
        if format in ['h', 'H'] and not raw_format:
            format_length = 2
        elif format in ['i', 'I', 'l', 'L', 'f'] and not raw_format:
            format_length = 4
        elif format in ['d', 'q', 'Q'] and not raw_format:
            format_length = 8
    
        if auto and not raw_format:
            b = self.f.read(4)
            
            if b == '':
                raise EOFError
            
            length = struct.unpack(self.endianness + 'i', b)[0]
            number = length / format_length
            
            b = self.f.read(length + 4)
            tmp = struct.unpack(self.endianness + format*number + 'i', b)
            length2 = tmp[-1]
            tmp = tmp[:-1]
        else:
            bytes_to_read = number * format_length + 8
            b = self.f.read(bytes_to_read)
            if b == '':
                raise EOFError

            fmt_string = self.endianness + "i"
            if raw_format:
                fmt_string += format + "i"
            else:
                fmt_string += format * number + "i"
            
            tmp = struct.unpack(fmt_string, b)
            length = tmp[0]
            length2 = tmp[-1]
            tmp = tmp[1:-1]
        
        assert length == length2
        
        if format == 's':
            # return just one string
            return ''.join(str(c) for c in tmp)
        elif number == 1:
            # just return the number and not a tuple containing just the number
            return tmp[0]
        else:
            # convert tuple to list
            return list(tmp)
        
    def read_headers(self):
        """Read and save the MCNP version and problem description from the
        Ptrac file.
        """
        # mcnp version info
        self.mcnp_version_info = self.read_next('s', auto=True)
        # problem title
        self.problem_title = self.read_next('s', auto=True).strip()


        # ptrac input data. can be omitted for now,
        # but has to be parsed, because it has variable length.
        # Also, this is the first difference between a file generated
        # with 4-byte and 8-byte numbers.
        line = self.read_next('f', auto=True)
        # if this line doesn't consist of 10 floats, then we've read them with
        # the wrong byte length and re have to re-read them (and every
        # following float) with 8 bytes length.
        if len(line) != 10:
            self.eightbytes = True
            tmp = struct.pack(self.endianness + "f"*20, *line)
            line = list(struct.unpack(self.endianness + "d"*10, tmp))

        # the first item is always 13. afterwards, there is 13 times the
        # following scheme:
        # N x_0 ... x_N,
        # where N is the number of values for the current input variable and
        # the x_i are its N values.
        num_variables = int(line[0]) # should always be 13.
        current_pos = 1
        current_variable = 1

        while current_variable <= num_variables:
            n = int(line[current_pos])
            if current_variable < num_variables and (current_pos + n + 1) >= len(line):
                line += self.read_next('f', 10)
            current_pos += n + 1
            current_variable += 1
    
    def read_variable_ids(self):
        """Read the list of variable IDs that each record type in the Ptrac
        file is comprised of. The variables can vary for different problems.
        Consult the MCNP manual for details.
        """
        
        variable_nums = dict()
        variable_ids = dict()
        
        if self.eightbytes:
            variable_info = self.read_next("qqqqqqqqqqqiiiiiiiii", 124, raw_format=True)
        else:
            variable_info = self.read_next('i', 20)
        
        variable_nums["nps"] = variable_info[0]
        variable_nums["src"] = variable_info[1] + variable_info[2]
        variable_nums["bnk"] = variable_info[3] + variable_info[4]
        variable_nums["sur"] = variable_info[5] + variable_info[6]
        variable_nums["col"] = variable_info[7] + variable_info[8]
        variable_nums["ter"] = variable_info[9] + variable_info[10]
        
        num_vars_total = sum(variable_info[:11])
        
        if self.eightbytes:
            # only the NPS vars are in 8 byte, the other ones are still 4
            fmt_string = "q" * variable_info[0] + "i" * sum(variable_info[1:11])
            fmt_length = 8 * variable_info[0] + 4 * sum(variable_info[1:11])
            all_var_ids = self.read_next(fmt_string, fmt_length, raw_format=True)
        else:
            all_var_ids = self.read_next('i', num_vars_total)
        
        for l in ["nps", "src", "bnk", "sur", "col", "ter"]:
            variable_ids[l] = all_var_ids[:variable_nums[l]]
            all_var_ids = all_var_ids[variable_nums[l]:]
        
        self.variable_nums = variable_nums
        self.variable_ids = variable_ids
        
    def read_nps_line(self):
        """Read an NPS record and save the type of the next event.
        """
        nps_line = self.read_next('i', self.variable_nums["nps"])
        self.next_event = nps_line[1]
    
    def read_event_line(self, ptrac_event):
        """Read an event record and save it to a given PtracParticle instance.
        """
    
        # save for current event, because this record contains only the next event's type
        event_type = self.next_event
        
        if event_type == 1000:
            e = "src"
        elif event_type == 3000:
            e = "sur"
        elif event_type == 4000:
            e = "col"
        elif event_type == 5000:
            e = "ter"
        else:
            e = "bnk"
        
        evt_line = self.read_next('f', self.variable_nums[e])
        
        self.next_event = evt_line[0]
        
        for i in xrange(1, len(self.variable_ids[e])):
            if self.variable_ids[e][i] in self.variable_mappings:
                ptrac_event[self.variable_mappings[ self.variable_ids[e][i] ]] = evt_line[i]
        ptrac_event["event_type"] = event_type

    def write_to_hdf5_table(self, hdf5_table, print_progress=0):
        """Writes the events contained in this Ptrac file to a given HDF5
        table. The table must already exist and have rows that match the
        PtracEvent definition.
        If desired, the number of processed events can be printed to the
        console each N events by passing the print_progress=N parameter.
        """
        
        ptrac_event = hdf5_table.row
        counter = 0
        
        while True:
            try:
                self.read_nps_line()
            except EOFError:
                break # no more entries
            
            while self.next_event != 9000:
                self.read_event_line(ptrac_event)
                ptrac_event.append()
                
                counter += 1
                if print_progress > 0 and counter % print_progress == 0:
                    print "processing event", counter


def read_mcnp_inp(inp):
    """This function reads an MCNP inp file and returns a list of Materials
    material objects (for single density materials) and MultiMaterial objects
    (for multiple density materials). This function relys on
    mat_from_mcnp."""

    mat_lines = []  # line of lines that begin material cards
    densities = {}  # dictionary to be populated with material numbers and densities
    mat_nums = []  # list of material numbers to be printed to stdout
    material_list = []  # to be populated with material objectes and returned

    line_count = 1
    line = linecache.getline(inp, line_count)
    # scroll through every line of the mcnp inp file
    while line != '':
        line = linecache.getline(inp, line_count)
        # check to see if line contains a cell card. If so, grab the density.
        # information is stored in a dictionary where:
        # key = material number, value = list of densities
        if len(line.split()) > 3:
            if line.split()[0].isdigit() is True \
            and line.split()[1].isdigit() is True \
            and line[0:5] != '     ' \
            and line.split()[1] != '0':

                if line.split()[1] not in densities.keys():
                    densities[line.split()[1]] = [float(line.split()[2])]

                else:
                    same_bool = False
                    for j in range(0, len(densities[line.split()[1]])):
                        if abs((float(line.split()[2]) \
                                 - densities[line.split()[1]][j])\
                                 / float(line.split()[2])) < 1E-4:
                            same_bool = True

                    if same_bool == False:
                        densities[line.split()[1]]\
                                                .append(float(line.split()[2]))

        # check line to see if it contain a material card, in the form m* where *
        # is a digit. If so store the line number and material number
        if line.split() != []:
            if line.split()[0][0] == 'm' or line.split()[0][0] == 'M':
                if line.split()[0][1].isdigit() is True:
                    mat_lines.append(line_count)
                    mat_nums.append(line.split()[0][1:])

        line_count += 1
        line = linecache.getline(inp, line_count)

    for i in range(0, len(mat_nums)):
        if mat_nums[i] in densities.keys():
            material_list.append(mat_from_mcnp(inp, mat_lines[i], densities[mat_nums[i]]))
        else:
            material_list.append(mat_from_mcnp(inp, mat_lines[i]))

    return material_list


def mat_from_mcnp(filename, mat_line, densities='None'):
    """This is a function that recieves and MCNP input filename, the
    line number, and list of densities associated with the material and
    returns a material object. This function is typically called by
    read_mcnp_inp. If a material has multiple densities, a multimaterial
    object is returned."""

    data_string = linecache.getline(filename, mat_line).split('$')[0]
    # collect all material card data on one string
    line_index = 1
    line = linecache.getline(filename, mat_line + line_index)
    while line[0:5] == '     ':
        # make sure element/isotope is not commented out
        if line.split()[0][0] != 'c' and line.split()[0][0] != 'C':
            data_string += line.split('$')[0]
        line_index += 1
        line = linecache.getline(filename, mat_line + line_index)


   # create dictionaries nucvec and table_ids
    nucvec = {}
    table_ids = {}
    for i in range(1, len(data_string.split())):
        if i & 1 == 1:
            zzzaaam = str(nucname.zzaaam(int(data_string.split()[i].split('.')[0])))
            nucvec[zzzaaam] = float(data_string.split()[i+1])
            if len(data_string.split()[i].split('.')) > 1:
                table_ids[str(zzzaaam)] = data_string.split()[i].split('.')[1]

    # Check to see it material is definted my mass or atom fracs.
    # Do this by comparing the first non-zero fraction to the rest
    # If atom fracs, convert.
    nucvecvals = nucvec.values()
    n = 0
    isatom = 0 < nucvecvals[n]
    while 0 == nucvecvals[n]:
        n += 1
        isatom = 0 < nucvecvals[n]
    for value in nucvecvals[n+1:]:
        if isatom != (0 <= value):
            msg = 'Mixed atom and mass fractions not supported. See material defined on line {0}'.format(mat_line)
            warnings.warn(msg)

    # apply all data to material object
    if isatom:
        mat = Material()
        mat.from_atom_frac(nucvec)
    else:
        mat = Material(nucvec=nucvec)  # set nucvec attribute to the nucvec dict from above

    mat.attrs['table_ids'] = table_ids
    mat.attrs['mat_number'] = data_string.split()[0][1:]

    # collect metadata, if present
    attrs = ['source', 'comments', 'name']
    line_index = 1
    attrs_line = linecache.getline(filename, mat_line - line_index)
    # while reading non-empty comment lines
    while attrs_line.strip() not in set('cC') \
            and attrs_line.split()[0] in ['c', 'C']:
        if attrs_line.split()[0] in ['c', 'C'] \
                and len(attrs_line.split()) > 1:
            possible_attr = attrs_line.split()[1].split(':')[0].lower()
            if possible_attr in attrs:
                if possible_attr.lower() == 'comments':
                    comments_string = \
                    str(''.join(attrs_line.split(':')[1:]).split('\n')[0])
                    comment_index = 1
                    comment_line = linecache.getline(filename, \
                            mat_line - line_index + comment_index)
                    while comment_line.split()[0] in ['c', 'C']:
                        if comment_line.split()[1].split(':')[0].lower() in attrs:
                            break
                        comments_string += ' ' + ' '.join( \
                                comment_line.split()[1:])
                        comment_index += 1
                        comment_line = linecache.getline(filename, \
                                mat_line - line_index + comment_index)
                    mat.attrs[possible_attr] = comments_string
                else:
                    mat.attrs[possible_attr] = \
                    ''.join(attrs_line.split(':')[1:]).split('\n')[0]  # set metadata
        line_index += 1
        attrs_line = linecache.getline(filename, mat_line - line_index)

    # Check all the densities. If they are atom densities, convert them to mass
    # densities. If they are mass densities they willl be negative, so make
    # them positive.
    if densities != 'None':
        converted_densities = []
        for den in densities:
            if den <= 0:
                converted_densities.append(-1*float(den))
            else:
                converted_densities.append(mat.mass_density(float(den)))

        # check to see how many densities are associated with this material.
        # if there is more than one, create a multimaterial"""
        if len(converted_densities) == 1:
            mat.density = converted_densities[0]
            finished_mat = mat

        elif len(converted_densities) > 1:
            mat_dict = {}
            for density in converted_densities:
                mat2 = Material()
                mat2.comp = mat.comp
                mat2.atoms_per_mol = mat.atoms_per_mol
                mat2.mass = mat.mass
                mat2.attrs = mat.attrs
                mat2.density = density
                mat_dict[mat2] = 1
            finished_mat = MultiMaterial(mat_dict)
    else:
        finished_mat = mat

    return finished_mat

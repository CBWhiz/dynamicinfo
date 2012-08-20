#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 2 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

#Written by CBWhiz on 8/20/2012
from __future__ import division
import ctypes
from ctypes import c_char, c_byte, c_ubyte, c_short, c_ushort, c_long, c_longlong, c_ulong, c_ulonglong, c_char_p

import os, sys
def incseek(file, dest):
    """file.seek(), but written to work around .seek() large integer issues"""
    sought = 0
    file.seek(0)
    while sought < dest:
        remain = dest - sought
        step = min(remain, sys.maxint)
        #print step, sought, dest
        file.seek(step, os.SEEK_CUR)
        sought += step

#http://wiki.python.org/moin/ctypes
class SerializableStructure(ctypes.Structure):
    """Structure that knows how to read / write itself from/to a string, and provides useful utility functions"""
    def toString(self):
        return buffer(self)[:]
    def loadString(self, bytes):
        fit = min(len(bytes), ctypes.sizeof(self))
        ctypes.memmove(ctypes.addressof(self), bytes, fit)
    def _iterate_fields(self):
        allfields = []
        for klass in tuple(self.__class__.__bases__) + (self.__class__, ):
            allfields.extend(getattr(klass, '_fields_', []))
        for fdata in allfields:
            if len(fdata) == 2:
                fieldname, fieldtype = fdata
                fwidth = ctypes.sizeof(fieldtype) * 8
            elif len(fdata) == 3:
                fieldname, fieldtype, fwidth = fdata
            else:
                raise Exception("Incorrect _fields_ definition")
            yield fieldname, fieldtype, fwidth
            
    def offsetof(self, field):
        """Returns the starting byte offset of a field.
        
        Note that this takes into account bitfields, but in those cases the starting
        byte may not align with the bit position due to accuracy loss."""
        offset = 0
        for fieldname, fieldtype, fwidth in self._iterate_fields():
            if field == fieldname:
                return offset // 8 #Integer division
            offset += fwidth
            #TODO: deal with self._pack_
        raise Exception("Field %s not found in %s"%(field, self.__class__.__name__))
        
    def dump(self):
        print "%s at %s:"%(self.__class__.__name__, getattr(self, 'pos', None))
        for fieldname, fieldtype, fwidth in self._iterate_fields():
            print "\t0x%04x - %s: %s"%(
                self.offsetof(fieldname), fieldname, getattr(self, fieldname)
            )
            
class GUID(SerializableStructure):
    _fields_ = [
        ("data", c_byte*16),
    ]
    def __repr__(self):
        return "GUID (%s)"%(''.join(str(x) for x in self.data))

class VarStructureMixin(object):
    """Mixin that also reads fields defined in _var_fields.
    
    Structure is similar to ctype's _fields_ object"""
    _var_fields = [
    ]
    def loadString(self, input):
        super(VarStructureMixin, self).loadString(input)
        #And now read the variable width objects
        start = next = self.offsetof('data_length') + 4
        dl_rel = 0
        for name, type in self._var_fields:
            old_next = next
            if type is int:
                tmp, next = readVarIntegerBE(input, next)
                dl_rel += next - old_next
            elif type is str:
                tmp, next = readVarString(input, next)
                dl_rel += next - old_next
            else:
                buf = ctypes.create_string_buffer(input)
                if hasattr(type, '__ctype_be__'):
                    type = type.__ctype_be__
                tmp = type.from_buffer(buf, next)
                next += ctypes.sizeof(type)
            setattr(self, name, tmp)
        
    def dump(self):
        super(VarStructureMixin, self).dump()
        for var, type in self._var_fields:
            print "\t         %s: %s"%(var, getattr(self, var))
#http://code.google.com/p/py-misc-scripts/source/browse/parse_mbr.py
#0x00	1	status[7] (0x80 = bootable, 0x00 = non-bootable, other = invalid[8])
#0x01	3	sector address of first partition sector.[9] The format is described in the next 3 bytes.
#    0x01	1	head[10]
#    0x02	1	sector is in bits 5-0[11]; bits 9-8 of cylinder are in bits 7-6
#    0x03	1	bits 7-0 of cylinder[12]
#0x04	1	partition type[13]
#0x05	3	sector address of the last sector in the partition.[14] The format is described in the next 3 bytes.
#    0x05	1	head
#    0x06	1	sector is in bits 5-0; bits 9-8 of cylinder are in bits 7-6
#    0x07	1	bits 7-0 of cylinder
#0x08	4	LBA of first sector in the partition
#0x0C	4	sectors in partition
class CSHEntry(SerializableStructure):
    _pack_ = 1
    _fields_ = [
        ('csh', c_ubyte*3)
    ]
    
class PartitionEntry(SerializableStructure):
    _pack_ = 1
    _fields_ = [
        ('status', c_ubyte),            #1 byte
        ('begin_chs', CSHEntry),        #3 bytes
        ('type', c_ubyte),              #1 byte
        ('end_chs', CSHEntry),          #3 bytes
        ('begin_lba', c_ulong),         #4 bytes
        ('size_in_sectors', c_ulong),   #4 bytes
    ]
assert ctypes.sizeof(PartitionEntry) == 16

class MBR(SerializableStructure):
    _fields_ = [
        ("code", c_byte*440),
        ("disk_sig", c_ulong),
        ("blank", c_short),
        ("partitions", PartitionEntry*4),
        ("mbr_sig", c_ushort),
    ]
    def is_valid(self):
        return self.mbr_sig == 0xAA55
            
assert ctypes.sizeof(MBR) == 512
        
#http://hackipedia.org/Disk%20formats/Partition%20tables/Windows%20NT%20Logical%20Disk%20Manager/html,%20ldmdoc/technical/privhead.html
class VMDB(ctypes.BigEndianStructure, SerializableStructure):
    _pack_ = 1
    _fields_ = [
        ("magic", c_char*4),
        ("vblk_last_seq_num", c_ulong),  
        ("vblk_size", c_ulong),          #Size of each VBLK, in bytes
        ("vblk_offset", c_ulong),        #In bytes, from start of VMDB
        ("status", c_ushort),
        ("ver_major", c_ushort),
        ("ver_minor", c_ushort),
        ("disk_group_name", c_char*31),
        ("disk_group_id", c_char*64),
        #.....
        #There is more to this structure, but it doesn't matter to us.
    ]
    def is_valid(self):
        return self.magic == 'VMDB'
        
    def loadDisk(self, _disk, pos):
        self.pos = pos
        self._disk = _disk
        incseek(self._disk, pos)
        self.loadString(_disk.read(ctypes.sizeof(self)))
        if self.is_valid():
            self.blocks = self.get_vblk()
            
    def get_vblk(self):
        incseek(self._disk, self.pos)
        self._disk.seek(self.vblk_offset, os.SEEK_CUR)
        blocks = []
        blkid = 0
        while blkid < self.vblk_last_seq_num:
            b = VBLK()
            b.loadDisk(self._disk, self.vblk_size)
            blkid = b.seq_num
            if b.is_valid():
                blocks.append(b.get_subclass())
        return blocks
    

    
class VBLK(ctypes.BigEndianStructure, VarStructureMixin, SerializableStructure):
    _pack_ = 1
    _fields_ = [
        ('magic', c_char*4),
        ('seq_num', c_ulong),
        ('group_num', c_ulong),
        ('record_num', c_ushort),
        ('record_count', c_ushort),
        ('update_status', c_ushort),
        ('record_flags', c_ubyte),
        ('record_type', c_ubyte),
        ('data_length', c_ulong),
    ]
    
    def get_subclass(self):
        #Note that each subclass may have multiple versions. That is not taken into account here.
        rt = self.record_type & 0xF
        rklass = {
            1: VBLKVolume,
            2: VBLKComponent,
            3: VBLKPartition,
            4: VBLKDisk,
            5: VBLKDiskGroup
        }
        klass = rklass.get(rt, self.__class__)
        nc = klass()
        nc.loadString(self._fulldata)
        nc.pos = self.pos
        nc._size = self._size
        nc._disk = self._disk
        return nc
            
    def is_valid(self):
        return self.magic == 'VBLK' and self.record_count > 0
        
    def loadDisk(self, _disk, size):
        self._size = size
        self._disk = _disk
        self.pos = _disk.tell()
        blockdata = _disk.read(size)
        self.loadString(blockdata)
        self._fulldata = blockdata

def readVarString(data, offset):
    """Reads a variable length string from data at a given offset. Returns (str, nextoffset)"""
    len = ord(data[offset])
    return (data[offset+1:offset+1+len], offset+1+len)
    
def readVarIntegerBE(data, offset):
    """Reads a variable length string from data at a given offset. Returns (value, nextoffset)"""
    len = ord(data[offset])
    ret = 0
    for i, d in enumerate(reversed(data[offset+1:offset+1+len])):
        place = 2**(i*8)
        ret += ord(d) * place
    return (ret, offset+1+len)
    
class VBLKVolume(VBLK):
    _fields_ = []
    _var_fields = [
        ('object_id', int),
        ('name', str),
        ('type', str),
        ('zero', c_ubyte),
        ('state', c_char*14),
        ('type_b', c_ubyte),
        ('vol_number', c_ubyte),
        ('zeros', c_ubyte*3),
        ('flags', c_ubyte),
        #('children_count', c_long),
        #('log_commit_id', c_ulonglong),
        #('unknown_id', c_ulonglong),
        #('size', int),
        #('partition_type', c_ubyte),
    ]
    def treeformat(self):
        typestr = dict(enumerate(['Unknown', 'Stripe', 'Basic / Spanned', 'RAID']))
        return "%s: %s (%s %s) (#%s)"%(self.__class__.__name__, self.name, self.type, self.state.value, self.vol_number.value)
class VBLKComponent(VBLK):
    _fields_ = []
    _var_fields = [
        ('object_id', int),
        ('name', str),
        ('state', str),
        ('type', c_ubyte),
        ('zeros', c_ulong),
        ('children_count', int),
        ('log_commit_id', c_ulonglong),
        ('zeros2', c_ulonglong),
        ('parent_id', int),
        ('zero3', c_ubyte)
    ]
    def treeformat(self):
        typestr = dict(enumerate(['Unknown', 'Stripe', 'Basic / Spanned', 'RAID']))
        return "%s: %s (%s %s)"%(self.__class__.__name__, self.name, self.state, typestr.get(self.type.value, 'Unknown type %s'%(self.type.value)))
class VBLKPartition(VBLK):
    _fields_ = []
    _var_fields = [
        ('object_id', int),
        ('name', str),
        ('zeros', c_ulong),
        ('log_commit_id', c_ulonglong),
        ('start', c_ulonglong),
        ('volume_offset', c_ulonglong),
        ('size', int),
        ('parent_id', int),
        ('disk_object_id', int),
    ]
    def treeformat(self):
        SECTOR_SIZE = 512
        part = self
        humansize = "%s gb"%(part.size * SECTOR_SIZE / 1024 / 1024 / 1024)
        extents_sectors = (part.volume_offset.value, part.volume_offset.value + part.size)
        extents = [x*SECTOR_SIZE for x in extents_sectors]
        return "%s: %s %s covering %s - %s on disk %s"%(self.__class__.__name__, self.name, humansize, extents[0], extents[1], self.disk_object_id)
class VBLKDisk(VBLK):
    _fields_ = []
    _var_fields = [
        ('object_id', int),
        ('name', str),
        ('disk_id', str),
        ('alt_name', str),
        ('zeros', c_long),
        ('log_commit_id', c_longlong),
    ]
    def treeformat(self):
        return "%s: %s (%s) {%s}"%(self.__class__.__name__, self.name, self.object_id, self.disk_id)
class VBLKDiskGroup(VBLK):
    _fields_ = []
    _var_fields = [
        ('object_id', int),
        ('name', str),
        ('disk_group_id', str),
    ]
    def treeformat(self):
        return "%s: %s {%s}"%(self.__class__.__name__, self.name, self.disk_group_id)
class TocBlock(ctypes.BigEndianStructure, SerializableStructure):
    _pack_ = 1
    _fields_ = [
        ("magic", c_char*8),
        ("seq_num", c_ulong),
        ("unk_0c", c_ulong),
        ("seq_num2", c_ulong),
        ("unk_14", c_ulong*4),
        ("bitmap0_name", c_char*8),
        ("bitmap0_flags", c_ushort),
        ("bitmap0_start", c_ulonglong),
        ("bitmap0_size", c_ulonglong),
        ("bitmap0_flags2", c_ulonglong),
        ("bitmap1_name", c_char*8),
        ("bitmap1_flags", c_ushort),
        ("bitmap1_start", c_ulonglong),
        ("bitmap1_size", c_ulonglong),
        ("bitmap1_flags2", c_ulonglong),
    ]
    def get_bitmap_info(self):
        bitmaps = {}
        for i in range(2):
            bitmaps[getattr(self, 'bitmap%s_name'%(i))] = {
                'name': getattr(self, 'bitmap%s_name'%(i)),
                'start': getattr(self, 'bitmap%s_start'%(i)),
                'size': getattr(self, 'bitmap%s_size'%(i)),
                'f1': getattr(self, 'bitmap%s_flags'%(i)),
                'f2': getattr(self, 'bitmap%s_flags2'%(i)),
            }
        return bitmaps
    def is_valid(self):
        return self.magic == 'TOCBLOCK'
assert ctypes.sizeof(TocBlock) == 0x68

class PrivHead(ctypes.BigEndianStructure, SerializableStructure):
    _pack_ = 1
    _fields_ = [
        ("magic", c_char*8),
        ("unk_008", c_long),
        ("ver_major", c_short),
        ("ver_minor", c_short),
        ("timestamp", c_longlong),
        ("unk_018", c_longlong),
        ("unk_020", c_longlong),
        ("unk_028", c_longlong),
        ("disk_id", c_char*64),
        ("host_id", c_char*64),
        ("disk_group_id", c_char*64),
        ("disk_group_name", c_char*32),
        ("unk_110", c_short),
        ("unk_112", c_byte*9),
        ("logical_disk_start", c_ulonglong),
        ("logical_disk_size", c_ulonglong),
        ("config_start", c_ulonglong),
        ("config_size", c_ulonglong),
        ("toc_count", c_ulonglong),
        ("toc_size", c_ulonglong),
        ("config_count", c_ulong),
        ("log_count", c_ulong),
        ("config_size", c_ulonglong),
        ("log_size", c_ulonglong),
        ("disk_sig", c_long),
        ("disk_set_guid", GUID),
        ("disk_set_guid2", GUID),
    ]
    def loadDisk(self, _disk, mypos=None):
        self._disk = _disk
        LBA = 512
        if not mypos:
            mypos = LBA*6
        self.pos = mypos
        
        incseek(_disk, self.pos)
        self.loadString(_disk.read(ctypes.sizeof(self)))
        if self.is_valid():
            #self.dump()
            self.tocblocks = self.get_tocblocks()
            tb = self.tocblocks[0]
            cfg = tb.get_bitmap_info()['config']
            
            base = self.config_start
            vmdb_sector = base + cfg['start']
            self._vmdb = VMDB()
            self._vmdb.loadDisk(_disk, LBA*vmdb_sector)
            if self._vmdb.is_valid():
                pass
                #for b in self._vmdb.blocks:
                #    b.dump()
        
    def get_version(self):
        ver = (self.ver_major, self.ver_minor)
        textver = {
            (2, 11): 'Windows 2000/XP',
            (2, 12): 'Windows Vista',
        }
        tv = textver.get(ver, '')
        if not tv:
            return "v%s.%s"%ver
        return "v%s.%s (%s)"%(ver[0], ver[1], tv)
        
    def get_tocblocks(self):
        ret = []
        offsets = [1, 2, 2045, 2046]
        base = self.config_start
        #import pdb; pdb.set_trace()
        for o in offsets:
            tb_base = base + o
            tb = TocBlock()
            LBA = 512
            pos = LBA*tb_base
            incseek(self._disk, pos)
            tb.loadString(self._disk.read(ctypes.sizeof(TocBlock)))
            if tb.is_valid():
                ret.append(tb)
        return ret
        
    def get_partitions(self):
        if not self.is_valid():
            return None
        parts = []
        for block in self._vmdb.blocks:
            if isinstance(block, VBLKPartition):
                parts.append(block)
        parts.sort(key=lambda o: o.start)
        return parts
            
    def is_valid(self):
        if not self.magic == 'PRIVHEAD':
            return False
        return True
#assert ctypes.sizeof(PrivData) == 0x187
    
class TreeNode(object):
    def __init__(self, data=None):
        self.data = data
        self.parent = None
        self.children = []
        
    def add_child(self, child):
        self.children.append(child)
        child.parent = self
        
    def remove_child(self, child):
        child.parent = None
        self.children.remove(child)

    def dump(self, level=0, include_root=True, initial_indent=0):
        indent = "   "*level
        indent += " "*initial_indent
        if include_root or level > 0:
            if self.data:
                print "%s%s"%(indent, self.data.treeformat() if hasattr(self.data, 'treeformat') else repr(self.data))
            else:
                print "%s%s"%(indent, repr(self))
        sortkey = lambda o: (o.data.__class__.__name__, o.data.name)
        for child in sorted(self.children, key=sortkey):
            child.dump(level+1, True, initial_indent=initial_indent)
        
def build_vblk_tree(blocks):
    root = TreeNode()
    objs = {}
    for b in blocks:
        if b.object_id:
            objs[b.object_id] = TreeNode(b)
    for b in objs.values():
        parent = objs.get(getattr(b.data, 'parent_id', None), root)
        parent.add_child(b)
    return root
    
class Disk(object):
    def __init__(self):
        self._mbr = MBR()
        self._privhead = PrivHead()
        self.name = ""
        
    def read(self, filename):
        self.__init__() #Clear data
        self._disk = None
        self._disk = open(filename, "rb")

        self.name = filename

        self._disk.seek(0)
        self._mbr.loadString(self._disk.read(512))
        
        self._privhead.loadDisk(self._disk)
            
    def dump(self):
        if self._privhead.is_valid():
            print "Dynamic Disk %s"%(self._privhead.get_version())
            print "\tDisk: %s {%s}"%(self.name, self._privhead.disk_id)
            print "\tDisk belongs to: %s {%s}"%(self._privhead.disk_group_name, self._privhead.disk_group_id)
            print "\tDatabase Tree Structure:"
            blocks = self._privhead._vmdb.blocks
            tree = build_vblk_tree(blocks)
            tree.dump(include_root=False, initial_indent=10)
        elif self._mbr.is_valid():
            print "MBR Disk %s"%(self.name)
        else:
            print "Invalid Disk %s"%(self.name)
            
def get_disk(number):
    #TODO: Allow linux /dev/ fienames
    d = Disk()
    d.read(r"\\.\PhysicalDrive%s"%(number))
    return d
    
if __name__ == '__main__':
    disk = {}
    for i in range(0, 10):
        try:
            d = get_disk(i)
            disk[i] = d
            d.dump()
            print
            print
        except IOError:
            break
    
    
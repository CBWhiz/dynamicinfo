dynamicinfo

===========



Dumps data about Windows Dynamic Disks, including which disk / partition holds which logical sectors and bytes

Notes
=====

The code here is quick and dirty, and not complete nor consise. With that said, it does work.

One possible use for this is to assist generating a linux compatable dmraid configuration file; see http://stackoverflow.com/questions/8427372/windows-spanned-disks-ldm-restoration-with-linux for more information.

It will also (theoreticly) work with linux if you replace the device filenames.

License
=======

GPLv2 or GPLv3, take your pick.

Output example
==============

<pre>
Invalid Disk \\.\PhysicalDrive0


MBR Disk \\.\PhysicalDrive1


Dynamic Disk v2.12 (Windows Vista)
        Disk: \\.\PhysicalDrive2 {08b31341-cae8-11e1-8ebf-0022159ae493}
        Disk belongs to: CBWHIZ-PC-Dg0 {08b3133c-cae8-11e1-8ebf-0022159ae493}
        Database Tree Structure:
             VBLKDisk: Disk1 (2) {08b3133d-cae8-11e1-8ebf-0022159ae493}
             VBLKDisk: Disk2 (6) {08b31341-cae8-11e1-8ebf-0022159ae493}
             VBLKDisk: Disk3 (15) {08b313c4-cae8-11e1-8ebf-0022159ae493}
             VBLKDiskGroup: CBWHIZ-PC-Dg0 {08b3133c-cae8-11e1-8ebf-0022159ae493}
             VBLKVolume: Volume1 (gen ACTIVE) (#1)
                VBLKComponent: Volume1-01 (ACTIVE Basic / Spanned)
                   VBLKPartition: Disk1-01 465.758789062 gb covering 0 - 500104691712 on disk 2
                   VBLKPartition: Disk2-02 89.5205078125 gb covering 500104691712 - 596226605056 on disk 6
                   VBLKPartition: Disk3-01 203.595703125 gb covering 596226605056 - 814835826688 on disk 15
             VBLKVolume: Volume2 (gen ACTIVE) (#1)
                VBLKComponent: Volume2-01 (ACTIVE Basic / Spanned)
                   VBLKPartition: Disk2-01 172.140625 gb covering 0 - 184834588672 on disk 6
                   VBLKPartition: Disk2-03 204.096679688 gb covering 184834588672 - 403981729792 on disk 6


Dynamic Disk v2.12 (Windows Vista)
        Disk: \\.\PhysicalDrive3 {08b313c4-cae8-11e1-8ebf-0022159ae493}
        Disk belongs to: CBWHIZ-PC-Dg0 {08b3133c-cae8-11e1-8ebf-0022159ae493}
        Database Tree Structure:
             VBLKDisk: Disk1 (2) {08b3133d-cae8-11e1-8ebf-0022159ae493}
             VBLKDisk: Disk2 (6) {08b31341-cae8-11e1-8ebf-0022159ae493}
             VBLKDisk: Disk3 (15) {08b313c4-cae8-11e1-8ebf-0022159ae493}
             VBLKDiskGroup: CBWHIZ-PC-Dg0 {08b3133c-cae8-11e1-8ebf-0022159ae493}
             VBLKVolume: Volume1 (gen ACTIVE) (#1)
                VBLKComponent: Volume1-01 (ACTIVE Basic / Spanned)
                   VBLKPartition: Disk1-01 465.758789062 gb covering 0 - 500104691712 on disk 2
                   VBLKPartition: Disk2-02 89.5205078125 gb covering 500104691712 - 596226605056 on disk 6
                   VBLKPartition: Disk3-01 203.595703125 gb covering 596226605056 - 814835826688 on disk 15
             VBLKVolume: Volume2 (gen ACTIVE) (#1)
                VBLKComponent: Volume2-01 (ACTIVE Basic / Spanned)
                   VBLKPartition: Disk2-01 172.140625 gb covering 0 - 184834588672 on disk 6
                   VBLKPartition: Disk2-03 204.096679688 gb covering 184834588672 - 403981729792 on disk 6


Dynamic Disk v2.12 (Windows Vista)
        Disk: \\.\PhysicalDrive4 {08b3133d-cae8-11e1-8ebf-0022159ae493}
        Disk belongs to: CBWHIZ-PC-Dg0 {08b3133c-cae8-11e1-8ebf-0022159ae493}
        Database Tree Structure:
             VBLKDisk: Disk1 (2) {08b3133d-cae8-11e1-8ebf-0022159ae493}
             VBLKDisk: Disk2 (6) {08b31341-cae8-11e1-8ebf-0022159ae493}
             VBLKDisk: Disk3 (15) {08b313c4-cae8-11e1-8ebf-0022159ae493}
             VBLKDiskGroup: CBWHIZ-PC-Dg0 {08b3133c-cae8-11e1-8ebf-0022159ae493}
             VBLKVolume: Volume1 (gen ACTIVE) (#1)
                VBLKComponent: Volume1-01 (ACTIVE Basic / Spanned)
                   VBLKPartition: Disk1-01 465.758789062 gb covering 0 - 500104691712 on disk 2
                   VBLKPartition: Disk2-02 89.5205078125 gb covering 500104691712 - 596226605056 on disk 6
                   VBLKPartition: Disk3-01 203.595703125 gb covering 596226605056 - 814835826688 on disk 15
             VBLKVolume: Volume2 (gen ACTIVE) (#1)
                VBLKComponent: Volume2-01 (ACTIVE Basic / Spanned)
                   VBLKPartition: Disk2-01 172.140625 gb covering 0 - 184834588672 on disk 6
                   VBLKPartition: Disk2-03 204.096679688 gb covering 184834588672 - 403981729792 on disk 6
</pre>
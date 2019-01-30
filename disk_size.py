import os
import psutil
import sys
from abc import ABC, abstractmethod
from collections import OrderedDict
from hurry.filesize import size
try:  # Workaround, because there isn't wmi module on Linux os.
    import wmi
except ModuleNotFoundError:
    pass


class DiskCheckerAbstractClass(ABC):

    def __init__(self, hard_drive=None):
        if hard_drive:
            self.check_specific_drive(hard_drive)
        else:
            self.check_disks()

    @abstractmethod
    def check_disks(self):
        pass

    @abstractmethod
    def check_specific_drive(self):
        pass


class LinuxOSDiskChecker(DiskCheckerAbstractClass):

    def check_disks(self, return_data=False):
        '''
        Check hard drives and their size on Linux OS.
        Returns all hard drive devices as dictionary if return_data is set to True.
        '''
        # Get all drives that are described as "disk" from lsblk
        # Example: ['sda': '232,9G'] (for one hard drive)
        hard_drives = [disk.strip().split(' ')
                       for disk in os.popen("lsblk -o NAME,TYPE,SIZE | grep 'disk'").readlines()]
        # Convert to list
        hard_drives_data = [['/dev/' + drive[0], drive[-1]] for drive in hard_drives]
        if return_data:
            return hard_drives_data

        print('You have {} hard {} installed: \n'.format(len(hard_drives_data),
                                                         'drives' if len(hard_drives_data) > 1
                                                         else 'drive'))
        for index, (drive_name, drive_size) in enumerate(hard_drives_data, start=1):
            print('{}. {} -> {}'.format(index, drive_name, drive_size))

    def check_specific_drive(self, inp):
        '''
        Return disk with details regarding partitions if available.
        :param inp: Could be either String which represents path (such as /dev/sda) or
        integer (number from the list of disks)
        '''
        try:  # If input is integer
            # Subtract 1 because of indexation.
            hard_drive_id = int(inp) - 1
            # Get list of all installed hard drives
            disks_list = self.check_disks(return_data=True)
            try:
                # Get details for respective hard drive id from disks_list
                # Also using index [0] to get only the path (such as '/dev/sda') for provided hard drive id
                hard_drive_path = disks_list[hard_drive_id][0]
            except IndexError:
                # If entered number does not exist
                print('Please enter the correct hard drive id!')
                # List all hard drives again for reference
                self.check_disks()
                return
        except ValueError:  # Input is string
            hard_drive_path = inp

        # Get partition details about given hard drive
        partitions = os.popen('lsblk {} -o NAME,TYPE,SIZE'.format(hard_drive_path)).readlines()

        if partitions:
            print('Below are the partitions for "/dev/{}" drive:'.format(partitions[1].split()[0]))
            print(''.join(x for x in partitions))
        else:
            print('Drive {} not found!'.format(inp))


class WindowsOSDiskChecker(DiskCheckerAbstractClass):
    try:  # Workaround, because wmi module isn't available on Linux os.
        cas = wmi.WMI ()
    except NameError:
        pass

    def check_disks(self, return_data=False):
        '''
        Check hard drives and their size on Windows OS.
        Returns all hard drive devices as dictionary if return_data is set to True.
        '''
        drives_data = [[index,
                        d.DeviceID.replace('.', '').replace('\\', ''),
                        d.Description, size(int(d.size))]
                       for index, d in enumerate(self.cas.Win32_DiskDrive(), start=1)]
        if return_data:
            # Get details about system's volumes
            volumes = [x for x in psutil.disk_partitions()]
            # Map volumes to hard drives
            [drive.append(volume) for (drive, volume) in zip(drives_data, volumes)]
            return drives_data

        print("You have {} hard drives installed".format(len(drives_data)))
        for drive in drives_data:
            print('  '.join([str(x) for x in drive]))
    
    def check_specific_drive(self, inp):
        '''
        Return disk with details regarding partitions if available.
        :param inp: integer - number from list of disks
        '''
        try:  # Check if entered numbed is whole number
            disk_id = int(inp) - 1
            hard_drives = self.check_disks(return_data=True)
            
            print("  ".join([str(field) for field in hard_drives[disk_id]]))
        except ValueError:  # If non numerical character is entered
            print("Please enter valid disk (whole) number! Reference below. \n")
            self.check_disks()
            return
        except IndexError:  # If disk number does not exist
            print("Disk with that index does not exist! Please try again.")
            self.check_disks()


if __name__ == '__main__':
    disk = sys.argv[1] if len(sys.argv) > 1 else None
    if os.name == 'posix':  # If Linux/ MacOS
        disc_checker = LinuxOSDiskChecker(disk)
    elif os.name == 'nt':  # If Windows
        disc_checker = WindowsOSDiskChecker(disk)
    else:
        print("OS not supported!")
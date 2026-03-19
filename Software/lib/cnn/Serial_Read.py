import serial # type: ignore
import serial.tools.list_ports # type: ignore
import os
import time
import re

DEF_TIME_FOR_NOW = time.localtime()
DEF_TIME_MONTH = str(DEF_TIME_FOR_NOW.tm_mon)
DEF_TIME_DAY = str(DEF_TIME_FOR_NOW.tm_mday)
#DEF_TIME_HOUR = str(DEF_TIME_FOR_NOW.tm_hour)
#DEF_TIME_MINUTE = str(DEF_TIME_FOR_NOW.tm_min)
DEF_FILE_NAME_SEPERATOR = '_'
DEF_SAVE_TO_PATH = './TraningData'+DEF_FILE_NAME_SEPERATOR + DEF_TIME_MONTH + DEF_FILE_NAME_SEPERATOR + DEF_TIME_DAY+'/'
#DEF_SAVE_TO_PATH = './TraningData_8_23/'
DEF_FILE_FORMAT = '.txt'
DEF_TITLE_STRING = 'Sampleing\n'
DEF_BAUD_RATE = 115200

motion_name = ['Lightning','Click','NoMotion']
port_list = list(serial.tools.list_ports.comports())

#显示所有可用串口
#Show all the port avaliable on current device
def show_all_com():
    index = 0
    port_list_name = []
    if len(port_list) <= 0:
        print("the serial port can't be found!")
    else:
        for itms in port_list:
            index += 1
            print(index,':',list(itms)[0], list(itms)[1])
            port_list_name.append(itms.device)

    return port_list_name

#请求用户根据索引值选择并初始化一个串口
#Ask a index number for serial port from user and initializes it.
def Serial_init():
    port_avaliable = show_all_com()
    port_avaliable_size = len(port_avaliable)
    index = int(input("\nChoose a port:"))

    while index > port_avaliable_size or index <= 0:
        if  index > port_avaliable_size or index <= 0:
            print("Invalid Input.Check and try again")
            index = int(input("Choose a port:"))
      
    print(f"\nSerial port",port_avaliable[index - 1],f"initalized successfully.\nBaud rate:{DEF_BAUD_RATE} Byte size:8  Parity:None  Stop bit:1")
    return serial.Serial(port=port_avaliable[index - 1],
                                baudrate=DEF_BAUD_RATE,
                                bytesize=serial.EIGHTBITS,
                                parity=serial.PARITY_NONE,
                                stopbits=serial.STOPBITS_ONE,
                                timeout=0.5) 
    
#检查数据串口数据标题是否符合定义的标题，数据的标题可以修改DEF_TITLE_STRING
#Check if the title from recerived data same as DEF_TITLE_STRING.
def Check_Title(Received_String):
    clean_received = Received_String.split('\n')[0].strip()
    clean_target = DEF_TITLE_STRING.strip()
    
    print(f"Received Title: '{clean_received}'") # 使用引号包裹，能看清是否有隐藏空格
    
    if clean_received == clean_target:
        return True
    else:
        return False

#从数据标题之后裁剪出可用的数据
#Cut off the tiltle from recerived data.
def IMU_String(Received_String):
    lines = Received_String.splitlines()
    if len(lines) > 1:
        # 丢弃第一行标题，合并剩余行
        return "\n".join(lines[1:]).lstrip() 
    return ""
    
#指定需要录制的动作名
#Assign a motion you wannna to record
def Motion_Assign():
    i = 0
    user_input = 0
    print('\nChoose one from the fllowing name')
    for i in range(len(motion_name)):
        print(i+1,motion_name[i])
    while user_input > len(motion_name) or user_input < 1:
        user_input = int(input("Assign a motion you want to decord (1-"+str(len(motion_name))+")"))
        if user_input > len(motion_name) or user_input < 1:
            print("Invalid Input.Check and try again")
        else:
                return user_input - 1            

    """
    寻找特定动作相关的文件中最大的数字。
    
    :param motion: 动作名称，应为'motion_name'列表中的一个元素。
    :param folder_path: 包含文件的目录路径。
    :return: 匹配文件中找到的最大数字，如果没有匹配的文件，则返回0。
    """
def find_max_number_in_filenames(motion, folder_path):

    max_number = 0
    number_pattern = re.compile(r'\d+')
    matching_filenames = []

    # 遍历指定文件夹中的所有文件
    for filename in os.listdir(folder_path):
        # 检查文件名是否包含特定的动作名称
        if motion in filename:
            matching_filenames.append(filename)

    # 在匹配的文件名中查找最大的数字
    for filename in matching_filenames:
        # 查找文件名中的所有数字
        numbers = number_pattern.findall(filename)
        # 更新最大数字
        for num_str in numbers:
            num = int(num_str)
            if num > max_number:
                max_number = num

    return max_number

#主函数
def main():
    serial_using = Serial_init()
    user_input = 'y'
    if not os.path.exists(DEF_SAVE_TO_PATH):
        os.mkdir(DEF_SAVE_TO_PATH)
    while user_input == 'y':
        motion_assigned = motion_name[Motion_Assign()]
        print(motion_assigned)
        recorded_count = 0
        name_index = find_max_number_in_filenames(motion_assigned,DEF_SAVE_TO_PATH) + 1
        data_set_max = int(input("How many data set you want to record:"))
        while recorded_count < data_set_max:
            received = serial_using.readall().decode("ASCII")
            if len(received) != 0:
                if Check_Title(received):
                    filename = DEF_SAVE_TO_PATH+motion_assigned+DEF_FILE_NAME_SEPERATOR+str(name_index)+DEF_FILE_FORMAT
                    with open(filename,"w") as file:
                        file.write(IMU_String(received))
                        file.close()
                    print("Saved as",filename)
                    recorded_count += 1
                    name_index += 1
                else:
                    print(received)
        print("Complete")
        user_input = input("Record another motion (y/n)")
    print("Bye!")

main()
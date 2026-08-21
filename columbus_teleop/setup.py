import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'columbus_teleop'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Manas Hanwat',
    maintainer_email='manashanwat@gmail.com',
    description=(
        'Custom keyboard teleoperation node for the Columbus Maximus '
        'differential drive robot. Publishes geometry_msgs/msg/Twist '
        'messages on /cmd_vel.'
    ),
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'teleop_node = columbus_teleop.teleop_node:main',
        ],
    },
)

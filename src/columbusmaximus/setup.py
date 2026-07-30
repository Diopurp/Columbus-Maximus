import os
from glob import glob
from setuptools import setup

package_name = 'columbusmaximus'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
    ('share/ament_index/resource_index/packages',
        ['resource/' + package_name]),

    ('share/' + package_name, [
        'package.xml',
        'model.config',
        'model.sdf'
    ]),

    (os.path.join('share', package_name, 'description'),
        glob('description/*.xacro') + glob('description/*.urdf')),

    (os.path.join('share', package_name, 'meshes'),
        glob('meshes/*.stl')),

    (os.path.join('share', package_name, 'launch'),
        glob('launch/*.launch.py')),

    (os.path.join('share', package_name, 'rviz'),
        glob('rviz/*.rviz')),
],

    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='tejoshnanda_chilakalapudi',
    maintainer_email='tejoshnanda.chilakalapudi@gmail.com',
    description='Columbus Maximus robot description',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [],
    },
)

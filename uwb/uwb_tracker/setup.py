from setuptools import find_packages, setup

package_name = 'uwb_tracker'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='durva',
    maintainer_email='durva@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'uwb_node = uwb_tracker.uwb_node:main',
            'uwb_node_rviz = uwb_tracker.uwb_node_rviz:main',
        ],
    },
)

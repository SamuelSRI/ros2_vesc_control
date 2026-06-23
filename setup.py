import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'rover_vesc_control'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),
        (
            'share/' + package_name,
            ['package.xml']
        ),
        (
            os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')
        ),
        (
            os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')
        ),
    ],
    install_requires=[
        'setuptools',
        'pyserial',
    ],
    zip_safe=True,
    maintainer='Samuel Gendre',
    maintainer_email='samuel16.gendre@gmail.com',
    description='ROS 2 VESC UART controller for tracked rover',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'vesc_tracks_node = rover_vesc_control.vesc_tracks_node:main',
        ],
    },
)
from setuptools import find_packages, setup

package_name = 'arm_driver'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sid-jetson',
    maintainer_email='sid-jetson@todo.todo',
    description='6DOF arm driver using PCA9685',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'arm_driver = arm_driver.arm_driver_node:main',
            'teleop = arm_driver.teleop_node:main',
            'bridge = arm_driver.bridge_node:main',
            'fake_controller = arm_driver.fake_controller_node:main',
        ],
    },
)

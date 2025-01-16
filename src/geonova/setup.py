from setuptools import setup, find_packages

setup(
    name='geo_nova',
    version='0.1.0',
    packages=find_packages('script'),  # 'script' 디렉터리에서 패키지 검색
    package_dir={'': 'script'},        # 'script' 기준으로 패키지 설치
    install_requires=[
        'rospy',       # 필요한 Python 패키지를 여기에 추가
        'std_msgs'
    ],
    author='dbparkJ',
    author_email='pjmsm0319@gmail.com',
    description='GeoNova ROS Package Utilities',
    license='BSD',
    keywords=['ROS', 'Python', 'GeoNova'],
)
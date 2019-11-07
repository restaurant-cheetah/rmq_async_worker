import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='rmq_async_worker',
    version='0.1',
    author='Dmitry Rubinstein',
    author_email='rubinsteindb@gmail.com',
    description='RMQ Microservice scaffold',
    packages=setuptools.find_packages(),
    install_requires=[
        'pika ~= 1.1',
    ],
)

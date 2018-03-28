FROM continuumio/miniconda3

MAINTAINER Guillaume Florent <florentsailing@gmail.com>

# toolchain
# ENV CXX=g++-7
# ENV CC=gcc-7

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:ubuntu-toolchain-r/test && \
    apt-get update && \
    apt-get install -y --allow-unauthenticated wget git build-essential libgl1-mesa-dev libfreetype6-dev libglu1-mesa-dev libzmq3-dev libsqlite3-dev libboost-all-dev libicu-dev python3-dev libgl2ps-dev libfreeimage-dev libtbb-dev g++ libopenblas-dev
RUN conda update -y conda && conda install -y -c conda-forge cmake=3.10.0 swig==3.0.12 ninja=1.8.2

# oce
WORKDIR /opt/build
RUN git clone https://github.com/tpaviot/oce && mkdir oce/build && mkdir oce/install
WORKDIR /opt/build/oce/build
RUN git checkout OCE-0.18.3 && \
    cmake -G Ninja \
      -DCMAKE_BUILD_TYPE=Release \
      -DOCE_TESTING:BOOL=OFF \
      -DOCE_BUILD_SHARED_LIB:BOOL=ON \
      -DOCE_VISUALISATION:BOOL=ON \
      -DOCE_DATAEXCHANGE:BOOL=ON \
      -DOCE_OCAF:BOOL=ON \
      -DOCE_DRAW:BOOL=OFF \
      -DOCE_WITH_GL2PS:BOOL=ON \
      -DOCE_WITH_FREEIMAGE:BOOL=ON \
      -DOCE_MULTITHREAD_LIBRARY:STRING="TBB" \
      -DOCE_INSTALL_PREFIX=/opt/build/install/oce \
 .. && \
 ninja install && \
 echo "/opt/build/install/oce/lib" >> /etc/ld.so.conf.d/pythonocc.conf && \
 ldconfig

# pythonocc
WORKDIR /opt/build
RUN git clone https://github.com/tpaviot/pythonocc-core
WORKDIR /opt/build/pythonocc-core
RUN git submodule update --init --remote --recursive
WORKDIR /opt/build/pythonocc-core/build
RUN cmake -G Ninja \
      -DOCE_INCLUDE_PATH=/opt/build/install/oce/include/oce \
      -DOCE_LIB_PATH=/opt/build/install/oce/lib \
      -DPYTHONOCC_BUILD=Release \
      -DPYTHONOCC_WRAP_OCAF=ON \
      # -DPYTHONOCC_WRAP_SMESH=ON \
      # -DSMESH_INCLUDE_PATH=/opt/build/install/smesh/include/smesh \
      # -DSMESH_LIB_PATH=/opt/build/install/smesh/lib \
    .. && \
    ninja install

# Run pythonocc tests
RUN cd /opt/build/pythonocc-core/test && python core_wrapper_features_unittest.py

# Other conda packages
RUN conda install -y numpy
RUN conda install -y matplotlib
RUN conda install -y pyqt

# ccad
WORKDIR /opt/build
ADD https://api.github.com/repos/osv-team/ccad/git/refs/heads/master version.json
RUN git clone --depth=1 https://github.com/osv-team/ccad
RUN cp -r /opt/build/ccad/ccad /opt/conda/lib/python3.6/site-packages

# RUN python /opt/build/ccad/unittest/test_all.py
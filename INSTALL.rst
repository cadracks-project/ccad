Install ccad
************

The simplest way to install **ccad** is by creating a Docker image that sets up the required environment.

Note that the *./install_ccad.sh* script maps the $HOME directory of the host machine to the $HOME folder of the Docker container. This means that the $HOME folder of the
host machine and the $HOME of the ccad Docker container share the same files and folders.

Installation steps
------------------

- Install `Docker <https://docs.docker.com/install/>`_ for your platform

- *git clone https://github.com/osv-team/ccad* somewhere under $HOME

- *cd ccad*

- *./install_ccad.sh*

- *./start_ccad.sh*

Now you can execute examples from ccad or write your own examples.


Development environment
-----------------------

After launching the ccad Docker container (*./start_ccad.sh* command) you can type the following command at the container prompt:

*export PYTHONPATH="${PYTHONPATH}:/home/<user>/path/to/ccad/"*

This will allow you to have changes to the ccad package code taken into account for tests and examples.

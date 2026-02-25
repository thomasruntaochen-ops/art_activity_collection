# install miniforge, which installs mamba
mkdir ~/miniforge
cd ~/miniforge
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"

bash Miniforge3-$(uname)-$(uname -m).sh
source ~/.zshrc # automatically source env

# install packages
mamba install numpy
mamba install pandas
mamba install jupyter
mamba install ipympl
mamba install plotly
#mamba install kaleido
mamba install scikit-image
mamba install fastapi uvicorn sqlalchemy pydantic pydantic-settings pymysql httpx beautifulsoup4 playwright tenacity openai pytest ruff

## Install playwright to simulate the browser activity 
pip install -e .\[crawler\] # run in the Dev/GitHub/art_activity_collection root directory
playwright install chromium

## Install mysql
Homebrew service:
    brew update
    brew install mysql
    brew services start mysql
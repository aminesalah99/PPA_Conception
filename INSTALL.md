
# Installation Guide for Dental Design Application

This guide will help you install and set up the Dental Design Application on your system.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation Steps

### 1. Download the Application

You can download the application in two ways:

#### Option A: Download from GitHub Repository

1. Go to the GitHub repository: https://github.com/yourusername/ppa_conception
2. Click the green "Code" button
3. Select "Download ZIP"
4. Extract the ZIP file to your desired location

#### Option B: Clone the Repository

If you have Git installed, you can clone the repository:

```
git clone https://github.com/yourusername/ppa_conception.git
cd ppa_conception
```

### 2. Set Up a Virtual Environment (Recommended)

It's recommended to use a virtual environment to keep dependencies isolated:

#### For Windows:

```
python -m venv venv
venv\Scripts\activate
```

#### For Linux/macOS:

```
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

Once the virtual environment is activated, install the required packages:

```
pip install -r src/requirements.txt
```

### 4. Run the Application

After installing the dependencies, you can run the application:

```
python src/main.py
```

## Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError: No module named 'Pillow'"

This error means the Pillow library is not installed. Install it using:

```
pip install Pillow
```

#### 2. "ModuleNotFoundError: No module named 'tkinter'"

On some Linux distributions, tkinter is not installed by default. Install it using:

- For Ubuntu/Debian:
  ```
  sudo apt-get install python3-tk
  ```

- For Fedora:
  ```
  sudo dnf install python3-tkinter
  ```

- For CentOS/RHEL:
  ```
  sudo yum install python3-tkinter
  ```

#### 3. Permission Errors

If you encounter permission errors when installing packages, try using the `--user` flag:

```
pip install --user -r src/requirements.txt
```

Or use sudo (on Linux/macOS):

```
sudo pip install -r src/requirements.txt
```

#### 4. Virtual Environment Activation Issues

If you can't activate the virtual environment:

- Make sure you're in the correct directory
- Check that the virtual environment folder exists
- For Windows, try using `venv\Scripts\activate.bat` instead of `venv\Scripts\activate`

### Getting Help

If you encounter issues not covered in this guide:

1. Check the [README.md](README.md) file for general information
2. Look at the [Issues](https://github.com/yourusername/ppa_conception/issues) section on GitHub
3. Create a new issue with detailed information about your problem

## Post-Installation Setup

### First Launch

1. Run the application using `python src/main.py`
2. Select between upper or lower dental arch design
3. Follow the on-screen instructions

### Configuration

The application will create a configuration file at `src/config/app_config.json` after the first launch. You can modify this file to customize various settings.

### Database Setup

The application will automatically create the necessary database files in the `elements_valides` directory on first run.

## Advanced Installation

### For Developers

If you're a developer and plan to modify the application:

1. Clone the repository
2. Set up a virtual environment
3. Install the development dependencies:
   ```
   pip install -r src/requirements.txt
   ```
4. Install the application in development mode:
   ```
   pip install -e .
   ```
5. Make your changes
6. Run tests (if available)

### Using Docker

You can also run the application using Docker (if a Dockerfile is provided):

1. Build the Docker image:
   ```
   docker build -t dental-design-app .
   ```
2. Run the container:
   ```
   docker run -it --rm dental-design-app
   ```

## Uninstallation

To uninstall the application:

1. Delete the application directory
2. If you installed it using pip with the `--user` flag:
   ```
   pip uninstall dental-design-app
   ```
3. If you used a virtual environment, simply delete the virtual environment folder

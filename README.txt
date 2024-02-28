# Eye-Tracking Image Generation Application

This is a Python application that uses the tkinter library for its GUI and involves image generation and manipulation. It uses a Tobii eye tracker to adjust the zoom level of the generated images based on the user's gaze. The application also uses JSON files to configure certain aspects of the image generation process.

## Installation

To install the necessary dependencies, run the following command:

```sh
pip install tkinter PIL tobii_research

Usage
To run the application, execute the main.py script:

This will open the application's GUI where you can interact with the image generation and manipulation features. The application will use the Tobii eye tracker to adjust the zoom level of the images based on where you are looking.

Configuration
The application uses JSON files for configuration. These files are located in the project's root directory and have names like TurboWithCLIP.json, SDXLTurboImgtoImg3.json, and TurbowithCLIP2.json. Each JSON file contains a series of inputs and class types that control various aspects of the image generation process.

Contributing
Contributions are welcome. Please open an issue to discuss your idea before making a pull request.

License
This project is licensed under the MIT License - see the LICENSE.md file for details.
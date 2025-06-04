# Soldered MicroPython Modules

![](https://github.com/SolderedElectronics/Soldered-MicroPython-modules/blob/main/img/soldered_micropython.png)

---

## Overview
A collection of MicroPython drivers and modules for Soldered products. This library aims to provide plug-and-play support for sensors, displays, actuators, and other peripherals used with Soldered development boards. 

---

## About
Soldered MicroPython Modules is an open-source library of MicroPython drivers developed and maintained by Soldered for our range of DIY electronics modules, sensors, and development boards. The goal is to make it easy for makers, educators, and engineers to get started quickly with Soldered hardware using MicroPython—whether for prototyping, classroom learning, or embedded projects.

Each module in the library is designed to be lightweight, readable, and compatible with a wide range of MicroPython-compatible microcontrollers.

---

## Installation
You can install a specific module using mpremote or manually downloading specific files onto the board using an IDE such as [Thonny](https://thonny.org/)

### Installing using mpremote (recommended)
After [**installing the mpremote package**](https://docs.micropython.org/en/latest/reference/mpremote.html), flash a module to the board using the following command:

```sh
  mpremote mip install github:SolderedElectronics/Soldered-Micropython-modules/main/ENTER-MODULE-HERE
```
For example, downloading the BME280 module looks like this:

```sh
  mpremote mip install github:SolderedElectronics/Soldered-Micropython-modules/main/BME280
```

The module can now be imported and used on your board:
```python
from bme280 import BME280
```

### Installing using an IDE ([Thonny](https://thonny.org/))

1. **Connect your board** to your computer via USB.
2. Open **Thonny**, and make sure the correct interpreter is selected:
   - Go to **Tools > Options > Interpreter**
   - Select "MicroPython (Raspberry Pi Pico / ESP32 / etc.)"
   - Choose the correct port and click **OK**
3. Open the `modules/` folder from this library on your computer.
4. For each module you want to use:
   - Open the `.py` file (e.g., `shtc3.py`) in Thonny
   - Go to **File > Save As...**
   - Choose **MicroPython device**
   - Save the file inside the `/lib/` directory on the device (create it if it doesn’t exist)
5. Once the modules are on your board, you can import them in your MicroPython scripts like any other module: 
```python
from bme280 import BME280
```
**Note:** When manually installing the modules you must also manually install any dependancies a module might use, those can be found in the package.json file in any module folder:

```json
"deps": [
    ["github:SolderedElectronics/Soldered-Micropython-modules/main/Qwiic/Qwiic.py", "main"]
  ],
```

---

## Structure

Each Module has its own folder with its respective package.json for usage with the above mentioned **mpremote installation**. There is also the module itself as well as a folder with examples of using the modules
The structure is as follows:

```
Module_Name/
   |
   +--- package.json  <-- Configuration file used by the mpremote package, contains dependencies and links to download module remotely
   |
   +--- Module_Name/
   |      +--- Module_Name.py  <-- The MicroPython module
   |      |
   |      `--- Examples/
   |            |--- Module_Example.py	<-- An example of how to use the respective module 
   |
```

---

## About Soldered

<img src="https://soldered.com/productdata/2023/01/soldered-logo-og.png" alt="soldered-logo" width="500"/>

At Soldered, we design and manufacture a wide selection of electronic products to help you turn your ideas into acts and bring you one step closer to your final project. Our products are intented for makers and crafted in-house by our experienced team in Osijek, Croatia. We believe that sharing is a crucial element for improvement and innovation, and we work hard to stay connected with all our makers regardless of their skill or experience level. Therefore, all our products are open-source. Finally, we always have your back. If you face any problem concerning either your shopping experience or your electronics project, our team will help you deal with it, offering efficient customer service and cost-free technical support anytime. Some of those might be useful for you:

- [Web Store](https://www.soldered.com/shop)
- [Documentation](https://soldered.com/documentation/)
- [Community & Technical support](https://soldered.com/community)

---

## Open-source license

Soldered invests vast amounts of time into hardware & software for these products, which are all open-source. Please support future development by buying one of our products.

This repository is under the MIT license, for more info, see [LICENSE](/LICENSE). Long story short, use these open-source files for any purpose you want to, as long as you apply the same open-source licence to it and disclose the original source. No warranty - all designs in this repository are distributed in the hope that they will be useful, but without any warranty. They are provided "AS IS", therefore without warranty of any kind, either expressed or implied. The entire quality and performance of what you do with the contents of this repository are your responsibility. In no event, Soldered (TAVU) will be liable for your damages, losses, including any general, special, incidental or consequential damage arising out of the use or inability to use the contents of this repository.

---

## Have fun!

And thank you from your fellow makers at Soldered Electronics.

 


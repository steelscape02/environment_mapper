# Environment Mapper Project

**The ability to scan an environment in 3D can take your project to the next dimension.. Literally.**

Unfortunately, prebuilt LiDAR scanning systems are very cost prohibitive for hobbyists and small teams. That's why we designed a **3D LiDAR environment mapping system** based on an STM32, TFMini LiDAR, and 2 SG90 mini servos.
This project is designed to be highly portable. Just design a power network as outlined in the `shield` folder, attach the noted hardware (see _Assembly_), upload the STM32 project in `firmware` to your own STM32, and viola!
You now have a functional 3D environment mapper.

To make this project more interactive, a desktop app is also included in this repo, designed to be a companion to the hardware, translating the points over UART and displaying them in a point cloud right on your computer.
Utilizing the lightweight OpenGL C++ framework, this app can achieve a 100Hz refresh rate and a rotatable model using GLM.

## Assembly

### Components

To build the environment mapper, you will need the following equipment:

- STM32 Nucleo L476RG Development Board (or equivalent)
- 2 SG90 mini servos
- 1 TFMini v2 LiDAR
- 1 pan/tilt mount (this [adafruit mount](https://www.adafruit.com/product/1967#:~:text=Technical%20Details.%20Dimensions%3A%20*%20Base%3A%2037mm%20x,36mm%20%2F%201.5%22x%201.4%22%20*%20Weight%3A%2037g) is a good option)

For the power network and connections, you can either get the equipment below or fabricate a shield using the files in the `shield` directory:

- 1 breadboard
- 5V 3A power supply, and breadboard connector
- jumper cables

### Optional Components

To improve the power distribution to the servos and LiDAR, we included bulk and local decoupling capacitors. If you want to include these capacitors:

- 3 1uF _ceramic_ capacitors (faster transient response)
- 1 100uF _electrolytic_ capacitor (bigger bulk storage)

## Citations

If you use this project or Open3D, please cite:

```bibtex
@article{Zhou2018,
  author = {Qian-Yi Zhou and Jaesik Park and Vladlen Koltun},
  title = {{Open3D}: {A} Modern Library for {3D} Data Processing},
  journal = {arXiv:1801.09847},
  year = {2018},
}
```

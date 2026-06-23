# Margot Color Converter

A lightweight, dark-themed Python utility built to reverse-engineer color blending for garment printing. 

When injecting translucent inks (like Sublimation or standard DTG without a white base) into colored fabrics, the shirt color acts as a physical filter, heavily altering the final printed result. Margot Color Converter mathematically pre-shifts the pixels in your transparent `.png` designs to compensate for the specific hex code of the target garment, ensuring the final physical print matches your intended artwork.

## Setup

Open a terminal in 'Margot Color Converter' Folder and run the following command:

```bash
mag -s 

or 

mag --setup
```

or in a powershell
```powershell
./mag -s 

or 

./mag --setup
```

## Run Software

After setup run: 
```bash
mag -r

or 

mag --run
```
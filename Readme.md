# Malware Detection using CNN: Analysis and Frontend Design Plan

## Overview

This document provides a comprehensive analysis of the existing machine learning model (`main.ipynb`) and its corresponding dataset (`raw_pe_images.csv`). It also outlines a detailed design plan for building a frontend application that interacts with this model.

The main problem addressed by this project is the increasing difficulty of detecting malicious software, especially new and modified malware variants. Traditional signature-based detection methods depend on previously known malware patterns and may fail when malware is altered or previously unseen. Therefore, there is a need for an effective automated approach that can identify malicious software accurately and distinguish it from legitimate software.

---

## Dataset

**Reference:** [https://ieee-dataport.org/open-access/malware-analysis-datasets-raw-pe-image](https://ieee-dataport.org/open-access/malware-analysis-datasets-raw-pe-image)

---

## Abstract

This dataset is part of my PhD research on malware detection and classification using Deep Learning. It contains static analysis data: Raw PE byte stream rescaled to a 32 x 32 greyscale image using the Nearest Neighbor Interpolation algorithm and then flattened to a 1024 bytes vector. PE malware examples were downloaded from virusshare.com. PE goodware examples were downloaded from portableapps.com and from Windows 7 x86 directories.

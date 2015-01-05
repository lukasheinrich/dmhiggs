#!/usr/bin/env python
import yoda
import argparse

parser = argparse.ArgumentParser(description='Calculating fiducial cross section from YODA input.')

parser.add_argument('input',type=str, help="YODA file containing Cutflow histogram")


def main():
  args = parser.parse_args()
  histos = yoda.readYODA(args.input)
  cutflow = histos['/DMHiggsFiducial/Cutflow']
  print '{} out of {} events passed the event selection'.format(cutflow.bins[-1].area,cutflow.bins[0].area) 
  efficiency = cutflow.bins[-1].area/cutflow.bins[0].area
  print 'fiducial efficiency is {}'.format(efficiency)
  
if __name__ == '__main__':
  main()
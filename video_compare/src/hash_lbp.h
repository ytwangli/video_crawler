#ifndef __HASH_LBP_H__
#define __HASH_LBP_H__

//#include <io.h>//win 
#include <stdio.h>
#include <string.h>
#include <string>

using namespace std;

#include <cv.h>
#include <cxcore.h>
#include <highgui.h>
#include <opencv2/opencv.hpp>
using namespace cv;

#define STRING_HASH_CODE	1

//uniform LBP ¾ùÔÈLBP
const uchar gLBP8U2[256] = {
	0, 1, 2, 3, 4, 58, 5, 6, 7, 58, 58, 58, 8, 58, 9, 10,
	11, 58, 58, 58, 58, 58, 58, 58, 12, 58, 58, 58, 13, 58, 14, 15,
	16, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58,
	17, 58, 58, 58, 58, 58, 58, 58, 18, 58, 58, 58, 19, 58, 20, 21,
	22, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58,
	58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58,
	23, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58,
	24, 58, 58, 58, 58, 58, 58, 58, 25, 58, 58, 58, 26, 58, 27, 28,
	29, 30, 58, 31, 58, 58, 58, 32, 58, 58, 58, 58, 58, 58, 58, 33,
	58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 34,
	58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58,
	58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 35,
	36, 37, 58, 38, 58, 58, 58, 39, 58, 58, 58, 58, 58, 58, 58, 40,
	58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 41,
	42, 43, 58, 44, 58, 58, 58, 45, 58, 58, 58, 58, 58, 58, 58, 46,
	47, 48, 58, 49, 58, 58, 58, 50, 51, 52, 58, 53, 54, 55, 56, 57 };


int countDifferentBit(int a,int b);
int pHashCode(char* imagePath, int* code, CvRect roi);
int getHanmingDistance(int* code1,int* code2);
#if STRING_HASH_CODE
string pHashCode(char* imagePath, CvRect roi);
int getHanmingDistance(string &str1,string &str2);
#endif
int getUniformLBP(IplImage *src, IplImage *dst, CvRect roi,const uchar *table);
int getLbpHist(char* imagePath,CvRect roi, float *hist,int mode);
void NormalizeHist(float *hist);
float compareHist(float *hist1,float *hist2, int histSize);

int getLbpSimilar(char* imagePath_a,CvRect roi_a,float *model_hist);
int getLbpSimilar(char* imagePath_a,CvRect roi_a,char* imagePath_b,CvRect roi_b);




#endif
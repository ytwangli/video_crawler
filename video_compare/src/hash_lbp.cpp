/*
 *yaning
 *2015.06.18
 */
#include "hash_lbp.h"


//count not same bit number
int countDifferentBit(int a,int b)
{
	int c = ~( ( ~(a | b) ) | (a & b) );
	int count = 0;
	
	while(c != 0) {
		if(c < 0) {
			count++;
		}
		c <<= 1;
	}//while
	return count;
}

 //pHash算法
int pHashCode(char* imagePath, int* code, CvRect roi)
{	
	Mat src,img ,dst;
	double dIdex[64];
	double mean = 0.0;
	int k = 0;
	int temp;
	
	IplImage *image = cvLoadImage(imagePath, -1);
	if(image == NULL) {
		printf("image load false : %s \n",imagePath);
		return (-1);
	}
	
	IplImage *gray = cvCreateImage(cvGetSize(image), image->depth, 1);
	if(image->nChannels != 1) {
		cvCvtColor(image, gray, CV_RGB2GRAY);
	}
	else {
		cvCopy(image,gray);
	}	
	//cvSmooth(gray,gray);//if use dct remove smooth yaning 2015.05.28
	src = gray;
	//src = Mat(cvGetSize(gray),CV_8UC1,gray->imageData);
	
	if((roi.width == 0) || (roi.height == 0) || (gray->width < (roi.x + roi.width)) || (gray->height < (roi.y + roi.height)) ) {
		img = Mat_<double>(src);
	}
	else {		
		img = Mat_<double>(src(roi));		
	}	
    /* 第一步，缩放尺寸，可以为Size(32,32)或Size(8,8)，也可以更高，主要是为了提高计算效率*/
	resize(img, img, Size(32,32)); 
	//img.resize(32); 	
    /* 第二步，离散余弦变换，DCT系数求取*/
	dct(img, dst);	
    /* 第三步，求取DCT系数均值（左上角8*8区块的DCT系数）*/
	for (int i = 0; i < 8; ++i) {
		for (int j = 0; j < 8; ++j) {
			dIdex[k] = dst.at<double>(i, j);
			mean += dst.at<double>(i, j)/64;
			++k;
		}
	}        
    /* 第四步，计算哈希值。*/
	for(int j = 0; j < 2; j++) {
		temp = 0;
		for (int i = 0;i < 32;i++) {
			if (dIdex[i + (j * 32)] >= mean) {
				temp += (1<<i);
			}
		}//for
		code[j] = temp;
	}//for
	
	src.release();
	img.release();
	dst.release();
	if(image != NULL) {
		cvReleaseImage(&image);
	}
	if(gray != NULL) {
		cvReleaseImage(&gray);
	}
	return 0;
}

//汉明距离计算
int getHanmingDistance(int* code1,int* code2)
{
 	int difference = 0;
	
	for(int i = 0; i < 2; i++) {
		difference += countDifferentBit(code1[i],code2[i]);
	}
	
 	return difference;
}
#if STRING_HASH_CODE
//pHash算法
string pHashCode(char* imagePath, CvRect roi)
{	
	Mat src,img ,dst;
	string rst(64,'\n');
	double dIdex[64];
	double mean = 0.0;
	int k = 0;
	
	IplImage *image = cvLoadImage(imagePath, -1);
	if(image == NULL) {
		printf("image load false : %s \n",imagePath);
		return "\n";
	}
	
	IplImage *gray = cvCreateImage(cvGetSize(image), image->depth, 1);
	if(image->nChannels != 1) {
		cvCvtColor(image, gray, CV_RGB2GRAY);
	}
	else {
		cvCopy(image,gray);
	}
	
	//cvSmooth(gray,gray);//if use dct remove smooth yaning 2015.05.28
	src = gray;
	//src = Mat(cvGetSize(gray),CV_8UC1,gray->imageData);
	
	if((roi.width == 0) || (roi.height == 0) || (gray->width < (roi.x + roi.width)) || (gray->height < (roi.y + roi.height)) ) {
		img = Mat_<double>(src);
	}
	else {		
		img = Mat_<double>(src(roi));		
	}
	
    /* 第一步，缩放尺寸，可以为Size(32,32)或Size(8,8)，也可以更高，主要是为了提高计算效率*/
	resize(img, img, Size(32,32)); 
	//img.resize(32); 	
    /* 第二步，离散余弦变换，DCT系数求取*/
	dct(img, dst);	
    /* 第三步，求取DCT系数均值（左上角8*8区块的DCT系数）*/
	for (int i = 0; i < 8; ++i) {
		for (int j = 0; j < 8; ++j) {
			dIdex[k] = dst.at<double>(i, j);
			mean += dst.at<double>(i, j)/64;
			++k;
		}
	}        
    /* 第四步，计算哈希值。*/
	for (int i = 0;i < 64;++i) {
		if (dIdex[i] >= mean) {
			rst[i]='1';
		}
		else {
			rst[i]='0';
		}
	}

	src.release();
	img.release();
	dst.release();
	if(image != NULL) {
		cvReleaseImage(&image);
	}
	if(gray != NULL) {
		cvReleaseImage(&gray);
	}
	return rst;
}

//汉明距离计算
int getHanmingDistance(string &str1,string &str2)
{
 	//if((str1.size() != 64) || (str2.size() != 64))
 	//	return -1;
 	int difference = 0;
 	for(int i = 0; i < 64; i++) {
 		if(str1[i] != str2[i])
 			difference++;
 	}
 	return difference;
}
#endif
//
int getUniformLBP(IplImage *src, IplImage *dst, CvRect roi,const uchar *table)
{
	CvRect rect = roi;
	if((src->width != dst->width) || (src->height != dst->height) || (src->widthStep != dst->widthStep) || (src->depth != dst->depth) || (src->nChannels != dst->nChannels))
	{
		return -1;
	}
	if((roi.width == 0) || (roi.height == 0) || (src->width < (roi.x + roi.width)) || (src->height < (roi.y + roi.height)) ) {
		rect = cvRect(0,0,src->width,src->height);
		//return -1;
	}
	
	uchar *data = (uchar*)src->imageData;  
    int step = src->widthStep;
		
	for(int y = (rect.y + 1); y <  (rect.y + rect.height - 1); y++)	{		
		for(int x = (rect.x + 1); x <  (rect.x + rect.width - 1); x++) {
			uchar neighbor[8] = {0};
			neighbor[0] = data[(y - 1) * step + (x - 1)];
			neighbor[1] = data[(y - 1) * step + (x)];
			neighbor[2] = data[(y - 1) * step + (x + 1)];
			neighbor[3] = data[(y) * step + (x + 1)];
			neighbor[4] = data[(y + 1) * step + (x + 1)];
			neighbor[5] = data[(y + 1) * step + (x)];
			neighbor[6] = data[(y + 1) * step + (x-1)];
			neighbor[7] = data[(y) * step + (x-1)];
			uchar center = data[(y) * step + (x)];
			uchar temp = 0;
			for(int k = 0; k < 8; k++) {
				temp += (neighbor[k] >= center) * (1 << k);  //计算LBP的值
			}
			dst->imageData[y * step + x] = table[temp];	//降为59维空间
		}
	}
	return 0;
}

//
int getLbpHist(char* imagePath,CvRect roi, float *hist,int mode)
{
	int step = 0;
	uchar *data = NULL;
	IplImage *srcLBP = NULL;
	CvRect rect = cvRect(0,0,0,0);

	IplImage *image = cvLoadImage(imagePath, -1);
	if(image == NULL) {
		printf("image load false : %s\n",imagePath);
		return -1;;
	}
	
	IplImage *gray = cvCreateImage(cvGetSize(image), image->depth, 1);		
	//cvCvtColor(image, gray, CV_RGB2GRAY);
	if(image->nChannels != 1) {
		cvCvtColor(image, gray, CV_RGB2GRAY);
	}
	else {
		cvCopy(image,gray);
	}
	
	cvSmooth(gray,gray);
	srcLBP = cvCreateImage(cvGetSize(gray), gray->depth, 1);

	if((roi.width == 0) || (roi.height == 0) || (image->width < (roi.x + roi.width)) || (image->height < (roi.y + roi.height)))	{
		rect = cvRect(0,0,gray->width,gray->height);		
	}
	else {		
		rect = roi;	
	}

	getUniformLBP(gray, srcLBP, rect,gLBP8U2);

	data = (uchar*)srcLBP->imageData;  
	step = srcLBP->widthStep;

	for(int y = (rect.y + 1);y < (rect.height - 1); y++ ) {
		for(int x = (rect.x + 1);x < (rect.width - 1); x++) {
			hist[data[y * step + x]] += 1;
			//*(hist + data[y * step + x]) += 1;
		}
	}

	if(mode) {
		NormalizeHist(hist);
	}

	if(image != NULL) {
		cvReleaseImage(&image);
	}
	if(gray != NULL) {
		cvReleaseImage(&gray);
	}
	if(srcLBP != NULL) {
		cvReleaseImage(&srcLBP);
	}
	return 0;
}

//
void NormalizeHist(float *hist)
{
	double sum = 0.0;
	float scalar = 0.0;

	for(int i = 0; i < 59; i++) {
		sum += hist[i];
	}
	scalar = (float)(1 / sum);

	for(int i = 0; i < 59; i++)	{
		hist[i] *= scalar;
	}
}

//
float compareHist(float *hist1,float *hist2, int histSize)
{
	int i = 0;
	float result = 0;

	for(i = 0; i < histSize; i++) {
		if( hist1[i] <= hist2[i] )
			result += hist1[i];
        else
            result += hist2[i];
	}
	
	return result;	
}

//
int getLbpSimilar(char* imagePath_a,CvRect roi_a,float *model_hist)
{
	float hist1[59] = {0.0};
	float similar_min = 0.0;

	getLbpHist(imagePath_a,roi_a, hist1,1);
	similar_min = compareHist(hist1,model_hist,59);

	if(similar_min > 0.87) {
		return 1;
	}
	else {
		return 0;
	}
}

//
int getLbpSimilar(char* imagePath_a,CvRect roi_a,char* imagePath_b,CvRect roi_b)
{
	float hist1[59] = {0.0};
	float hist2[59] = {0.0};
	float similar_min = 0.0;

	getLbpHist(imagePath_a,roi_a, hist1,1);
	getLbpHist(imagePath_b,roi_b, hist2,1);
	similar_min = compareHist(hist1,hist2,59);

	if(similar_min > 0.87) {
		return 1;
	}
	else {
		return 0;
	}
}







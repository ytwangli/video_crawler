/*
 *yaning
 *2015.06.13
 */
#include <unistd.h>
#include <cstdio>
#include <dirent.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <iostream>
#include <deque>
#include <list>
#include <vector> 
#include <pthread.h>

#include <cstdlib> 
#include <limits.h>
#include <sys/types.h>

#include "hash_lbp.h"

//-------------------------------
#define DEBUG				0
#define USE_SQLITE3			0
#define USE_MYSQL			1

#if	USE_SQLITE3
#include <sqlite3.h>
#endif

#if	USE_MYSQL
#include <mysql/mysql.h>
#endif

//--------------------------mysql-----------------------
#define HOST_R 				"10.121.86.156"   //"sh.videomonitor.r.qiyi.db"
#define HOST_W 				"10.121.86.156"   //"sh.videomonitor.w.qiyi.db"
#define USER 				"root"            //"videomonitor"
#define PASSWD 				"iloveiqiyi"      //"evPoLol4"
#define DB 				"mysql"	          //"videomonitor"
#define PORT 				3306
//#define PORT 				8597

#define LONG_CONNECT		0
//------------------------------
#define CODE_FLAG			1
#define USED_FLAG			1
#define NEW_FLAG			1
#define USED_FLAG_UPDATE	2
#define NEW_FLAG_UPDATE		1

//------------------------------
typedef struct _CodeKey{
	int count;
	int hashCode[2];
	float lbpCode[59];
	string path;
}CodeKey;

typedef struct _TableInfo{
	string m_strSite;
	string m_strImageDir;
	string m_strKeyType;	
	string m_strRoi;
	string m_strKeyPath;
	string m_strDate;
	string m_strOnlineTime;
	int m_iCodeFlag;
	int m_iUsedFlag;
	int m_iNewFlag;		
}TableInfo;

typedef struct _ThreadArgs{
	string m_strDatabase;
	string m_strTable;
	string m_strReportDir;
	int m_ihost;	
	pthread_mutex_t	m_mtx_lock;
	pthread_mutex_t m_mtx_file;
	pthread_cond_t m_cond;
	bool m_bReady;
	list< pair<TableInfo,list<TableInfo> > > m_lstObj;
	list<string> m_lstSrcKey;	
	list<string> m_lstObjKey;
}ThreadArgs;

typedef struct _ReportInfo{
	string m_strSite;	
	string m_strPath;
}ReportInfo;

typedef struct _CompareResult{
	string m_strSrc;	
	string m_strObj;
	int m_hash_dist;
	float m_lbp_sim;
	float m_ssim_sim;	
}CompareResult;

//---------------function-------------------------
void* thread_compare(void *arg);
void* thread_getImageList(void *arg);

void FormatDir(string& strDir);
int getDirList(string strDir,list<string> &pList);
int getFileList(string strDir,list<string> &pList);
int getFileList(string strDir,vector<string> &pList);
int getCodes(string dirPath, vector<CodeKey>& hashCodeList);

float deepCompare(char *path1,char *path2,CvRect roi);
Scalar getMSSIM(char * imagePatha,char * imagePathb,CvRect roi);
//int imageHist(char* imagePath,CvRect roi);
int imageHist(char* imagePath,CvRect roi_s,CvRect roi_d);


void removeAll(string &str,char c);
int compare_time(string &str1,string &str2);
int bitCount ( unsigned n );
//----------------------------------
int g_ihost = -1;
int g_threadNum = 4;
char g_inPath1[PATH_MAX];
char g_inPath2[PATH_MAX];

pthread_mutex_t g_mutex_file;
pthread_t tid_fileList;
pthread_t tid_compare[64];

char tableName_i[] = "iqiyidata";
char tableName_o[] = "pathdata";

CvRect g_rectRoi = cvRect(0,0,0,0);

float LBP_SIM = 0.85;
float MSSIM_SIM = 0.8;


//-------------------main--------------------------------------------
int main(int argc, char* argv[])
{		
	if(argc == 3){
		strcpy(g_inPath1,argv[1]); 		//report path
		g_ihost = atoi(argv[2]);		//host number
		printf("#input Path1 ->%s \n",g_inPath1);
	}
	else if(argc == 4){
		strcpy(g_inPath1,argv[1]);		//report path
		g_ihost = atoi(argv[2]);		//host number
		g_threadNum = atoi(argv[3]);	//thread number
		printf("#input Path1 ->%s \n",g_inPath1);
	}	
	else{
		cout<<"#please input correct path ! "<<endl;
		return -1;
	}
	
	//thread number
	if(g_threadNum < 1){
		g_threadNum = 4;
	}
	else if(g_threadNum > 64) {
		g_threadNum = 64;
	}
	
	DIR *pDir = opendir(g_inPath1);  
	if(pDir == NULL) {		
			mkdir(g_inPath1, S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH);	
	}
	closedir(pDir);
	
	//---------------------start--------------------------			
	//----------------ThreadArgs init---------------------
	ThreadArgs threadArgs;
	
	threadArgs.m_strDatabase.assign(DB);
	threadArgs.m_strTable.assign(g_inPath1);
	threadArgs.m_strReportDir.assign(g_inPath1);
	threadArgs.m_ihost = g_ihost;
	threadArgs.m_bReady = false;	
	
	pthread_mutex_init(&threadArgs.m_mtx_lock,NULL);
	pthread_mutex_init(&threadArgs.m_mtx_file,NULL);
	pthread_cond_init(&threadArgs.m_cond,NULL);			
	//create
	if (pthread_create(&tid_fileList, NULL, thread_getImageList, &threadArgs) != 0) {
		cout <<"#create thread failed !"<< endl;
		return -1;
	}
	
	for(int i = 0; i < g_threadNum; i++)	{
		if (pthread_create(&tid_compare[i], NULL, thread_compare, &threadArgs) != 0) {
			cout << "#create thread failed->" << i << endl;
			return -1;
		}
	}	
	//release	
	void *threadRet;
	pthread_join(tid_fileList,&threadRet);

	for(int i = 0; i < g_threadNum; ++i)	{
		void *threadRet1;
		pthread_join(tid_compare[i],&threadRet1);
	}	
	//release 	
	pthread_mutex_destroy(&threadArgs.m_mtx_lock);
	pthread_mutex_destroy(&threadArgs.m_mtx_file);	
	pthread_cond_destroy(&threadArgs.m_cond);
	
	cout<<"#all thread exit ..."<<endl;
#if DEBUG	
	printf("#all thread exit;%s(%d)-> %s exit ! \n",__FILE__,__LINE__,__FUNCTION__);
#endif	
	return 0;
}

void FormatDir(string& strDir)
{
	if (strDir.at(strDir.length() -1) != '\\' &&
		strDir.at(strDir.length() -1) != '/')
	{
		strDir += '/';
	}
}

//
int getDirList(string strDir,list<string> &pList)
{
	DIR *pDir;
	struct dirent *pDirent;		
	int rst = -1;
	
	if(!(pDir = opendir(strDir.c_str()))) {
		printf("#%s -> open file failed ! file->%s \n",__FUNCTION__,(char*)strDir.c_str());
		return -1;
	}
	string path = strDir;
	FormatDir(path);	
	while((pDirent = readdir(pDir)) != NULL) {  
        if(strcmp(pDirent->d_name, ".") == 0 || strcmp(pDirent->d_name, "..") == 0) {
			continue;
		}  
  
		string strFullPath = path + pDirent->d_name;
		struct stat stFile;		
		if( (stat(strFullPath.c_str(), &stFile) >= 0) && (S_ISDIR(stFile.st_mode)) ) {  
			pList.push_back(strFullPath);
			rst &= 0;
        }		      	 
    } //while 	
	closedir(pDir);
	return rst;
}

//
int getFileList(string strDir,list<string> &pList)
{
	DIR *pDir;
	struct dirent *pDirent;	
	string fType = ".key";
	int rst = -1;
	
	if(!(pDir = opendir((char*)strDir.c_str()))) {
		printf("#%s -> open file failed ! file->%s \n",__FUNCTION__,(char*)strDir.c_str());
		return -1;
	}
	string path = strDir;
	FormatDir(path);	
	while((pDirent = readdir(pDir)) != NULL) {  
        if(strcmp(pDirent->d_name, ".") == 0 || strcmp(pDirent->d_name, "..") == 0) {
			continue;
		}  
  
		string strFullPath = path + pDirent->d_name;
		struct stat stFile;		
		if( (stat(strFullPath.c_str(), &stFile) >= 0) && (S_ISDIR(stFile.st_mode)) ) {  
			//fileList(strFullPath,pList);
			continue;
        }
		else {
			if(strFullPath.substr(strFullPath.size() - fType.size() ) == fType){
				pList.push_back(strFullPath);
				rst &= 0;
			}
		}         	 
    } //while 
	
	closedir(pDir);
	return rst;
}

//
int getFileList(string strDir,vector<string> &pList)
{
	DIR *pDir;
	struct dirent *pDirent;	
	string fType = ".key";
	int rst = -1;
	
	if(!(pDir = opendir((char*)strDir.c_str()))) {
		printf("#%s -> open file failed ! file->%s \n",__FUNCTION__,(char*)strDir.c_str());
		return -1;
	}
	string path = strDir;
	FormatDir(path);	
	while((pDirent = readdir(pDir)) != NULL) {  
        if(strcmp(pDirent->d_name, ".") == 0 || strcmp(pDirent->d_name, "..") == 0) {
			continue;
		}  
  
		string strFullPath = path + pDirent->d_name;
		struct stat stFile;		
		if( (stat(strFullPath.c_str(), &stFile) >= 0) && (S_ISDIR(stFile.st_mode)) ) {  
			//fileList(strFullPath,pList);
			continue;
        }
		else {
			if(strFullPath.substr(strFullPath.size() - fType.size() ) == fType){
				pList.push_back(strFullPath);
				rst &= 0;
			}
		}         	 
    } //while 
	
	closedir(pDir);
	return rst;
}

//
int getCodes(string dirPath, vector<CodeKey>& CodeList)
{
	FILE *fp;
	int rst = -1;
	
	fp = fopen((char*)dirPath.c_str(),"r");
	if(fp == NULL) {
		perror("fopen");
		printf("#%s->open file failed->%s \n",__FUNCTION__,(char*)dirPath.c_str());
		return rst;
	}
	
	char path[256];
	CodeKey keyCode;
	while(!feof(fp)) {
		rst = fscanf( fp, "%d,%d,%d,",&keyCode.count,&keyCode.hashCode[0],&keyCode.hashCode[1] );
		if(feof(fp)) {
            rst = 0;
            break;
        }
        else if(!(rst > 0)) {
                rst = 1;
                break;                        
            }	
		//printf("hashCode[0] = %d,hashCode[1] = %d \n",keyCode.hashCode[0],keyCode.hashCode[1]);
		for( int i = 0; i < 59; i++ ) {
			rst = fscanf( fp, "%f,",&keyCode.lbpCode[i] );
			if(!(rst > 0)) {
                rst = 2;
                break;
			}
			//printf("lbpCode[%d] = %f \n",i,keyCode.lbpCode[i]);
		}
		if(fscanf( fp, "%s",path ) > 0) {
			keyCode.path.assign(path);
			CodeList.push_back(keyCode);
			rst = 0;
			//cout<<"get key code :"<<keyCode.path<<endl;
		}
		else {
            rst = 3;
            break;
        }		
	}//while 
	
	fclose(fp);
	return rst;
}

//
void* thread_compare(void *arg)
{
	if (!arg) {
		printf("#%s -> arg is null ! \n",__FUNCTION__);
		return((void *)0);
	}
	
	//-------------------ThreadArgs---------------
	ThreadArgs *_args = (ThreadArgs *)arg;
	
	//string &g_strDatabase = _args->m_strDatabase;
	//string &g_strTable = _args->m_strTable;
	int ihost = _args->m_ihost;
	string &g_strReportDir =  _args->m_strReportDir;
	pthread_mutex_t &g_mtx_lock = _args->m_mtx_lock;
	//pthread_mutex_t &g_mtx_lock_file = _args->m_mtx_file;
	pthread_cond_t &g_cond_ready = _args->m_cond;		
	bool &g_bReady = _args->m_bReady;
	list<string> &g_srcKeyFiles = _args->m_lstSrcKey;
	//list<string> &g_objKeyFiles = _args->m_lstObjKey;
	list< pair<TableInfo,list<TableInfo> > > &g_objFileList = _args->m_lstObj;
	
	//---------------------local--------------------------		
	FILE *fp;
	
	vector<CodeKey> vSrcCode;
	vector<CodeKey> vObjCode;	
	string sub_str_i;
	string sub_str_o;
	string g_reportFile;
	string srcFileName;
	string objFileName;
	//list<string> srcFileList;
	list<string> objFileList;
	
	TableInfo srcInfo;
	TableInfo objInfo;
	list<TableInfo> srcInfoList;
	
	list<string> g_lstNotUpdata_files;
	list<ReportInfo> g_lstPending_report_files;
	list<string> reportFiles;
	list< pair<string,vector<CodeKey> > > srcKeyinfo;
	
	int rst = -1;
	int pos = 0;
	char szSql[1024];
	
	TableInfo tInfo;
	string strTemp;
	//----------------------------mysql-----------------------------
	MYSQL tMysql;	
	
	//-----------------------------time-----------------------------------
	char* szTime = new char[100];
	char* szTime_s = new char[100];
	time_t now;
	struct tm* timeinfo;
	
	unsigned long long hash_count = 0;
	unsigned long long lbp_count = 0;
	unsigned long long sim_count = 0;
	
	//--------------------thread info-----------------------
	pthread_t pid = pthread_self();	
	//---------------------body-----------------------	
	pthread_mutex_lock(&g_mtx_lock);
	while(!g_bReady) {
		pthread_cond_wait(&g_cond_ready,&g_mtx_lock);
	}
	pthread_mutex_unlock(&g_mtx_lock);		
	
	//--------------------time-----------------------
	time(&now);
	timeinfo = localtime(&now);
	strftime(szTime,100,"%F %T",timeinfo);
	cout<<"#compare thread id->"<<pid<<"->start->"<<szTime<<endl;
	//------------------------------init mysql----------------------
#if LONG_CONNECT
	int flag = 0;
	mysql_init(&tMysql);
	//HOST_W->"sh.videomonitor.w.qiyi.db"; USER->"videomonitor"; PASSWD->"evPoLol4"; DB->"video_data"; PORT->8597
	for(int i = 0; i < 10; i++) {
		if(!mysql_real_connect(&tMysql,HOST_W,USER,PASSWD,DB,PORT,NULL,0)) {
			printf("Error connecting to database:%s\n",mysql_error(&tMysql));
			mysql_close(&tMysql);
			usleep(100000 * (i + 2));
		}
		else {
			flag = 1;
			mysql_query(&tMysql, "SET NAMES UTF8");
			cout<<"connect to database successfully!"<<endl;
			break;
		}
	}//for					
	
	if(flag != 1) { return 0; }
	
#endif
	//---------------------get iqiyi key codes----------------------
	for(list<string>::iterator iter = g_srcKeyFiles.begin(); iter != g_srcKeyFiles.end(); iter++) {
		string keyFile = *iter;
		rst = -1;
		vSrcCode.clear();		
		rst = getCodes(keyFile,vSrcCode);		
		if(rst == 0) {
			srcKeyinfo.push_back(make_pair(keyFile,vSrcCode));
		}
		else {
			cout<<"rst:"<<rst<<";get iqiyi key codes failed->"<<keyFile<<endl;
		}		
	}//for
	//---------------------while loop----------------------
	while(g_objFileList.size() > 0 ) {
		pair<TableInfo,list<TableInfo> > objInfoPair;
		pthread_mutex_lock(&g_mtx_lock);
		objInfoPair = g_objFileList.front();						
		g_objFileList.pop_front();			
		pthread_mutex_unlock(&g_mtx_lock);
		
		objInfo = objInfoPair.first;
		srcInfoList = objInfoPair.second;		
		objFileName = objInfo.m_strKeyPath;
		//srcFileList = objInfoPair.second;

		hash_count = 0;
		lbp_count = 0;
		sim_count = 0;
		time(&now);
		timeinfo = localtime(&now); 
		strftime(szTime_s,100,"%F %T",timeinfo); 
		
		pos = objFileName.find_last_of(".");
		string str_temp = objFileName.substr(0,pos);
		pos = str_temp.find_last_of("/");
		string file_name = str_temp.substr(pos + 1);
		string str_temp1 = str_temp.substr(0,pos);
		pos = str_temp1.find_last_of("/");
		string str_site = str_temp1.substr(pos + 1);
		sub_str_o.assign(str_site).append(file_name);	
	
		rst = -1;
		vObjCode.clear();			
		rst = getCodes(objFileName,vObjCode);
		if(rst != 0) {
			cout<<"rst:"<<rst<<";get other key codes failed->"<<objFileName<<endl;
			continue;
		}
		
		reportFiles.clear();
		//-------------------loop-----------------
		while(srcInfoList.size() > 0) {
			pthread_mutex_lock(&g_mtx_lock);
			srcInfo = srcInfoList.front();			
			srcInfoList.pop_front();
			pthread_mutex_unlock(&g_mtx_lock);
			
			srcFileName = srcInfo.m_strKeyPath;			
			pos = srcFileName.find_last_of(".");
			string sub_str = srcFileName.substr(0,pos);
			pos = sub_str.find_last_of("/");
			//sub_str_i.assign(sub_str.substr(pos + 1) ).append("_");
			sub_str_i.assign(sub_str.substr(pos + 1) ).append("/");
			g_reportFile.assign(g_strReportDir).append("/").append(sub_str_i).append(sub_str_o).append(".csv");
			string strSubdir;
			strSubdir.assign(g_strReportDir).append("/").append(sub_str_i);
			DIR *pSubDir = opendir(strSubdir.c_str());  
			if(pSubDir == NULL) {		
					mkdir(strSubdir.c_str(), S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH);	
			}
			else {
				closedir(pSubDir);
			}
						
			/*
			vSrcCode.clear();		
			getCodes(srcFileName,vSrcCode);
			*/
			for(list< pair<string,vector<CodeKey> > >::iterator iter = srcKeyinfo.begin(); iter != srcKeyinfo.end(); iter++) {
				if(strcmp( (char*)srcFileName.c_str(),(char*)iter->first.c_str()) == 0 ) {
					vSrcCode = iter->second;
					break;
				}
			}//for
			
			list<CompareResult> report_list;	//
			for(vector<CodeKey>::iterator iterObj = vObjCode.begin(); iterObj != vObjCode.end(); iterObj++) {
				CodeKey codeObj = *iterObj;			
				for(unsigned int j = 0; j < vSrcCode.size(); j++) {
					CodeKey codeSrc = vSrcCode[j];
					hash_count++;	
					if( (codeSrc.count >= ( ((codeObj.count - 4) > 0) ? (codeObj.count - 4) : 0) ) 
						&& (codeSrc.count <= ( ((codeObj.count + 4) < 64) ? (codeObj.count + 4) : 64) ) ) {
						//int distance = getHanmingDistance(codeSrc.hashCode,codeObj.hashCode);
						int hanming = codeSrc.hashCode[0] ^ codeObj.hashCode[0];
						int distance = bitCount ( hanming );
						hanming = codeSrc.hashCode[1] ^ codeObj.hashCode[1];
						distance += bitCount ( hanming );						
						if((distance >= 0 ) && (distance < 5) ) {
							float sim = compareHist(codeSrc.lbpCode,codeObj.lbpCode,59);
							lbp_count++;					
							if( (sim > LBP_SIM) || (distance == 0)) {
#if 1
								if( ( access((char*)codeSrc.path.c_str(),F_OK) != 0 ) || ( access((char*)codeObj.path.c_str(),F_OK) != 0)){ continue; }
#else
								if((fp = fopen((char*)codeSrc.path.c_str(),"r")) == NULL ) { continue;}	else { fclose(fp);}
								if((fp = fopen((char*)codeObj.path.c_str(),"r")) == NULL ) { continue;}	else { fclose(fp);}
#endif
								//add for deep compare
								float similar = deepCompare( (char*)codeSrc.path.c_str(), (char*)codeObj.path.c_str(), g_rectRoi );								
								sim_count++;
								if( similar > MSSIM_SIM) {									
									CompareResult result;
									result.m_strSrc.assign(codeSrc.path);
									result.m_strObj.assign(codeObj.path);
									result.m_hash_dist = distance;	
									result.m_lbp_sim = sim;	
									result.m_ssim_sim = similar;	
									report_list.push_back(result);
								}//if
																
							}//if
							
							if( (distance < 2) || (sim > 0.95) ) { break;	}
						}//if
					
					}//if
					
				}//for
				
			}//for
			//write file
			if(report_list.size() > 0) {
				cout<<"report list size:"<<report_list.size()<<endl;
				fp = fopen(g_reportFile.c_str(),"w");
				if(fp != NULL) {
					for(list<CompareResult>::iterator iter = report_list.begin(); iter != report_list.end(); iter++) {
						string str;
						stringstream ss;
						ss << iter->m_hash_dist;
						str.assign(iter->m_strSrc).append(",").append(iter->m_strObj).append(",hash,").append(ss.str());
						ss.clear();
						ss.str("");
						ss << iter->m_lbp_sim;					
						str.append(",lbp,").append(ss.str());
						ss.clear();
						ss.str("");
						ss << iter->m_ssim_sim;
						str.append(",similar,").append(ss.str()).append("\n");					
						fwrite((char*)str.c_str(),str.size(),1,fp);	//write file	
						ss.clear();
						ss.str("");
					}//for				
					fclose(fp);
					report_list.clear();
					reportFiles.push_back(g_reportFile);
				}
				else {
					cout<<"create file failed:"<<g_reportFile<<endl;
				}
				
			}//if(report_list.size() > 0)
				
		}//while(objFileList.size() > 0)
		//-------------now time--------------------				
		time(&now);
		timeinfo = localtime(&now); 
		strftime(szTime,100,"%F %T",timeinfo);
		cout<<"#Start:"<<szTime_s<<"->End:"<<szTime<<"->hash count:"<<hash_count<<"->lbp count:"<<lbp_count<<"->ssim count:"<<sim_count<<objFileName<<endl;

#if USE_MYSQL	
#if !LONG_CONNECT				
		mysql_init(&tMysql);
		//HOST_W->"sh.videomonitor.w.qiyi.db"; USER->"videomonitor"; PASSWD->"evPoLol4"; DB->"video_data"; PORT->8597
		if(!mysql_real_connect(&tMysql,HOST_W,USER,PASSWD,DB,PORT,NULL,0)) {
			printf("Error connecting to database:%s\n",mysql_error(&tMysql));
			mysql_close(&tMysql);
			string strRemove;			
			for(list<string>::iterator iter = reportFiles.begin(); iter != reportFiles.end(); iter++) {
				string RemoveFile = *iter;	
				if( (access(RemoveFile.c_str(),0) == 0) ) {
					strRemove.clear();
					strRemove.assign("rm ").append(RemoveFile);
					system((char*)strRemove.c_str());
				}
				usleep(1000);						
			}
			reportFiles.clear();
			break;
		}//if				
		mysql_query(&tMysql, "SET NAMES UTF8");
#endif
		while(reportFiles.size() > 0) {
			string UpdataFile = reportFiles.front();			
			reportFiles.pop_front();
			sprintf(szSql, "insert into compare_result(host,site,report_path,status,create_date,update_date) values(%d,'%s','%s',%d,'%s','%s');"
					, ihost, (char*)objInfo.m_strSite.c_str(), (char*)UpdataFile.c_str(),1,szTime,szTime);	
			rst = mysql_query(&tMysql,szSql);
			usleep(1000);						
		}

		sprintf(szSql, "UPDATE %s SET used_flag=%d,new_flag=%d,update_date='%s' WHERE host=%d AND key_path='%s';"
				, tableName_o, USED_FLAG_UPDATE,NEW_FLAG_UPDATE, szTime, ihost, (char*)objFileName.c_str() );		
		rst = mysql_query(&tMysql,szSql);
		if(rst != true) {
			printf("#%s(%d)->%s mysql update failed ! \n",__FILE__,__LINE__,__FUNCTION__);				
		}
#if !LONG_CONNECT
		mysql_close(&tMysql);
#endif
#endif			
		cout<<szTime<<"---compare a object key file ok->"<<objFileName<<endl;
	}//while(g_objFileList.size() > 0 )
#if LONG_CONNECT	
	mysql_close(&tMysql);
#endif
	//-------------now time--------------------
	time(&now);
	timeinfo = localtime(&now); 
	strftime(szTime,100,"%F %T",timeinfo); 
	cout<<"#sub thread exit->"<<szTime<<endl;
#if DEBUG	
	printf("#%s(%d)-> %s exit ! \n",__FILE__,__LINE__,__FUNCTION__);
#endif	
	delete[] szTime;
	delete[] szTime_s;	
	return ((void *) 0);
}




float deepCompare(char *path1,char *path2,CvRect roi)
{
	float similar = 0;	
	Scalar sim = Scalar::all(0);
	CvRect roi_temp;
	
	IplImage *image = cvLoadImage(path1, -1);
	if(image == NULL) {
		return similar;
	}

	if((roi.width == 0) || (roi.height == 0) || (image->width < (roi.x + roi.width)) || (image->height < (roi.y + roi.height)) )
	{
		roi_temp = cvRect(0,0,image->width,image->height);
	}
	else
	{		
		roi_temp = roi;		
	}
	
	if(image != NULL) {
		cvReleaseImage(&image);
	}	
	if( (imageHist(path1,roi_temp,roi_temp) == 0) && (imageHist(path2,g_rectRoi,g_rectRoi) == 0) ) {	
	//if( (imageHist(path1,roi_temp,roi_temp) == 0) && (imageHist(path2,g_rectRoi,roi_temp) == 0) ) {	
		sim = getMSSIM(path1,path2,g_rectRoi);
		if((sim.val[0] > 0.5) || (sim.val[1] > 0.5) || (sim.val[2] > 0.5)) {
			similar = (sim.val[0] > sim.val[1]) ? sim.val[0] :sim.val[1];
			similar = (similar > sim.val[2]) ? similar :sim.val[2];									
		}		
	}
	else {
		similar = 0;
	}
	return similar;
}


Scalar getMSSIM(char * imagePatha,char * imagePathb,CvRect roi)
{
	Scalar mssim = Scalar::all(0);
    //Mat i1=imread(imagePatha);
    Mat i2=imread(imagePathb);
	if(!i2.data){
		return mssim;
	}
	//--------------------for roi image----------------------------	
	CvRect roi_temp;
	Mat img_roi = imread(imagePatha);
	if(!img_roi.data){
		return mssim;
	}

	//cout<<"image mat img_roi.rows="<<img_roi.rows<<"; img_roi.cols="<<img_roi.cols<<endl;
	
	if((roi.width == 0) || (roi.height == 0) || (img_roi.cols < (roi.x + roi.width)) || (img_roi.rows < (roi.y + roi.height)) )
	{
		roi_temp = cvRect(0,0,img_roi.cols,img_roi.rows);
	}
	else
	{		
		roi_temp = roi;		
	}
	Mat i1 = img_roi(roi_temp);
	
	//Mat i1 = img_roi;
	
	//yaning 2015.06.19
	if((i1.rows != i2.rows) || (i1.cols != i2.cols)) {
		int rows = (i1.rows < i2.rows) ? i1.rows:i2.rows;
		int cols = (i1.cols < i2.cols) ? i1.cols:i2.cols;
		//resize(i1,i1,Size(rows,cols));
		//resize(i2,i2,Size(rows,cols));
		resize(i1,i1,Size(cols,rows));
		resize(i2,i2,Size(cols,rows));
	}
	//------------------------end roi image----------------------------
	
    const double C1 = 6.5025, C2 = 58.5225;
    int d = CV_32F;
    Mat I1, I2;
    i1.convertTo(I1, d);
    i2.convertTo(I2, d);
    Mat I2_2   = I2.mul(I2);
    Mat I1_2   = I1.mul(I1);
    Mat I1_I2  = I1.mul(I2);
    Mat mu1, mu2;
    GaussianBlur(I1, mu1, Size(11, 11), 1.5);
    GaussianBlur(I2, mu2, Size(11, 11), 1.5);
    Mat mu1_2   =   mu1.mul(mu1);
    Mat mu2_2   =   mu2.mul(mu2);
    Mat mu1_mu2 =   mu1.mul(mu2);
    Mat sigma1_2, sigma2_2, sigma12;
    GaussianBlur(I1_2, sigma1_2, Size(11, 11), 1.5);
    sigma1_2 -= mu1_2;
    GaussianBlur(I2_2, sigma2_2, Size(11, 11), 1.5);
    sigma2_2 -= mu2_2;
    GaussianBlur(I1_I2, sigma12, Size(11, 11), 1.5);
    sigma12 -= mu1_mu2;
    Mat t1, t2, t3;
    t1 = 2 * mu1_mu2 + C1;
    t2 = 2 * sigma12 + C2;
    t3 = t1.mul(t2);
    t1 = mu1_2 + mu2_2 + C1;
    t2 = sigma1_2 + sigma2_2 + C2;
    t1 = t1.mul(t2);
    Mat ssim_map;
    divide(t3, t1, ssim_map);
    mssim = mean( ssim_map );
	//yaning
	I1.release();
	I2.release();
	I2_2.release();
    I1_2.release();
    I1_I2.release();
    mu1.release();
	mu2.release();
	mu1_2.release();
    mu2_2.release();
    mu1_mu2.release();
    sigma1_2.release();
	sigma2_2.release(); 
	sigma12.release();
	t1.release();
	t2.release();
	t3.release();
	ssim_map.release();
    return mssim;
}



int imageHist(char* imagePath,CvRect roi_s,CvRect roi_d)
{
	int rst = -1;
	int step = 0;
	CvRect roi_temp;
	CvRect roi_temp2;

	IplImage *image = cvLoadImage(imagePath, -1);
	if(image == NULL) {
		printf("image load false : %s\n",imagePath);
		return -1;;
	}
	if((roi_d.width == 0) || (roi_d.height == 0) || (image->width < (roi_d.x + roi_d.width)) || (image->height < (roi_d.y + roi_d.height)) )
	{
		roi_temp = cvRect(0,0,image->width,image->height);
	}
	else
	{		
		roi_temp = roi_d;		
	}
	if((roi_s.width == 0) || (roi_s.height == 0) || (image->width < (roi_s.x + roi_d.width)) || (image->height < (roi_s.y + roi_d.height)) )
	{
		roi_temp2 = cvRect(0,0,image->width,image->height);
	}
	else
	{		
		roi_temp2 = roi_s;		
	}
	
	IplImage *gray = cvCreateImage(Size(roi_temp.width,roi_temp.height), image->depth, 1);
	IplImage *gray_temp = cvCreateImage(cvGetSize(image), image->depth, 1);
	if(image->nChannels != 1) {
		cvCvtColor(image, gray_temp, CV_RGB2GRAY);
	}
	else {
		cvCopy(image,gray_temp);
	}
		
	cvSetImageROI(gray_temp, roi_temp2); 
	cvResize(gray_temp,gray);
	 
	step = gray->widthStep;
	float sum_b = 0;
	float sum_w = 0;
	float sum_g[6] = {0};
	int imageSize = gray->width * gray->height;
	
	for(int y = 0;y < gray->height; y++ ) {
		for(int x = 0;x < gray->width; x++) {
			if(gray->imageData[y * step + x] < 10) {
				sum_b += 1;
			}
			else if(gray->imageData[y * step + x] > 245) {
				sum_w += 1;
			}
			else if(gray->imageData[y * step + x] < 50) {
				sum_g[0] += 1;
			}
			else if(gray->imageData[y * step + x] < 90) {
				sum_g[1] += 1;
			}
			else if(gray->imageData[y * step + x] < 130) {
				sum_g[2] += 1;
			}
			else if(gray->imageData[y * step + x] < 170) {
				sum_g[3] += 1;
			}
			else if(gray->imageData[y * step + x] < 200) {
				sum_g[4] += 1;
			}
			else {
				sum_g[5] += 1;
			}
		}
	}//for

	if( (sum_b / imageSize) > 0.85 ){
		rst = -1;	
	}
	else if( (sum_w / imageSize) > 0.85 ){
		rst = -1;
	}	
	else if( (sum_g[0] / imageSize) > 0.75 ){
		rst = -1;
	}
	else if( (sum_g[1] / imageSize ) > 0.75 ){
		rst = -1;
	}
	else if( (sum_g[2] / imageSize ) > 0.75 ){
		rst = -1;
	}
	else if( (sum_g[3] / imageSize ) > 0.75 ){
		rst = -1;
	}
	else if( (sum_g[4] / imageSize ) > 0.75 ){
		rst = -1;
	}
	else if( (sum_g[5] / imageSize ) > 0.75 ){
		rst = -1;
	}
	else {
		rst = 0;
	}
	
	if(image != NULL) {
		cvReleaseImage(&image);
	}
	if(gray != NULL) {
		cvReleaseImage(&gray);
	}
	if(gray_temp != NULL) {
		cvReleaseImage(&gray_temp);
	}
	
	return rst;
}


void* thread_getImageList(void *arg)
{
	if (!arg) {
		printf("#%s ->arg is null ! \n",__FUNCTION__);
		return((void *)1);
	}
	//ThreadArgs
	ThreadArgs *_args = (ThreadArgs *)arg;
	
	//string &g_strDatabase = _args->m_strDatabase;
	//string &g_strTable = _args->m_strTable;
	//string &g_strReportDir = _args->m_strReportDir;
	int ihost = _args->m_ihost;
	pthread_mutex_t &g_mtx_lock = _args->m_mtx_lock;
	pthread_cond_t &g_cond_ready = _args->m_cond;
	
	bool &g_bReady = _args->m_bReady;	
	list<string> &g_srcKeyFiles = _args->m_lstSrcKey;
	list<string> &g_objKeyFiles = _args->m_lstObjKey;
	list< pair<TableInfo,list<TableInfo> > > &g_objFileList = _args->m_lstObj;
		
	char szSql[1024];
	unsigned int iRowNum = 0;
	unsigned int iFieldsNum = 0;
		
	list<TableInfo> iqiyi_images;
	list<TableInfo> other_images;
	list<TableInfo> objFileList;
	//list<string> objFileList;
	
#if USE_MYSQL
	MYSQL tMysql;
    MYSQL_RES *pRres;
    MYSQL_ROW tRow;
		
	mysql_init(&tMysql);
	//HOST_R->"sh.videomonitor.r.qiyi.db"; USER->"videomonitor"; PASSWD->"evPoLol4"; DB->"videomonitor"; PORT->8597
	if(!mysql_real_connect(&tMysql,HOST_R,USER,PASSWD,DB,PORT,NULL,0)) { 
		mysql_close(&tMysql);		
		pthread_mutex_lock(&g_mtx_lock);
		g_bReady = true;
		pthread_mutex_unlock(&g_mtx_lock);
		pthread_cond_broadcast(&g_cond_ready);		
		printf("Error connecting to database:%s\n",mysql_error(&tMysql));
		return ((void *)0);		
    }
    	
    mysql_query(&tMysql, "SET NAMES UTF8");
	//------------------------------------iqiyi------------------------------------------
	//sprintf(szSql, "SELECT * FROM %s WHERE host=%d AND code_flag=1 AND used_flag=1;", tableName_i, ihost);
	sprintf(szSql, "SELECT site,image_dir,key_type,key_path,new_flag,online_time FROM %s WHERE host=%d AND code_flag=%d AND used_flag=%d;"
			, tableName_i, ihost, CODE_FLAG, USED_FLAG);
	mysql_query(&tMysql,szSql);	
	pRres = mysql_store_result(&tMysql);
	//pRres = mysql_use_result(&tMysql);
	iFieldsNum = mysql_num_fields(pRres);
	iRowNum = mysql_num_rows(pRres); 
	printf("#iqiyi->row:%d column=%d\n",iRowNum,iFieldsNum); 
	
	iqiyi_images.clear();
	while (NULL != (tRow = mysql_fetch_row(pRres)) ){
		TableInfo args;
		if(tRow[0] != NULL) {
			args.m_strSite.assign(tRow[0]);
		}
		if(tRow[1] != NULL) {
			args.m_strImageDir.assign(tRow[1]);
		}
		if(tRow[2] != NULL) {
			args.m_strKeyType.assign(tRow[2]);
		}				
		if(tRow[3] != NULL) {
			args.m_strKeyPath.assign(tRow[3]);			
		}
			
		args.m_iNewFlag = atoi(tRow[4]);
		
		if(tRow[5] != NULL) {
			args.m_strOnlineTime.assign(tRow[5]);
			removeAll(args.m_strOnlineTime,'-');
		}
		
		iqiyi_images.push_back(args);
		g_srcKeyFiles.push_back(args.m_strKeyPath);
	}//while
	mysql_free_result(pRres);
	
	//------------------------------------other------------------------------------------
	//sprintf(szSql, "SELECT * FROM %s WHERE host=%d AND code_flag=1 AND used_flag=1;", tableName_o, ihost);
	sprintf(szSql, "SELECT site,image_dir,key_type,key_path,new_flag,date_str FROM %s WHERE host=%d AND code_flag=%d AND used_flag=%d AND new_flag=%d order by date_str desc LIMIT 16;"
			, tableName_o, ihost, CODE_FLAG, USED_FLAG, NEW_FLAG);
	mysql_query(&tMysql,szSql);	
	pRres = mysql_store_result(&tMysql);
	//pRres = mysql_use_result(&tMysql);
	iFieldsNum = mysql_num_fields(pRres);
	iRowNum = mysql_num_rows(pRres); 
	printf("#other->row:%d column=%d\n",iRowNum,iFieldsNum); 
	
	other_images.clear();
	while (NULL != (tRow = mysql_fetch_row(pRres)) ){
		TableInfo args_o;	
		if(tRow[0] != NULL) {
			args_o.m_strSite.assign(tRow[0]);
		}
		if(tRow[1] != NULL) {
			args_o.m_strImageDir.assign(tRow[1]);
		}
		if(tRow[2] != NULL) {
			args_o.m_strKeyType.assign(tRow[2]);
		}				
		if(tRow[3] != NULL) {
			args_o.m_strKeyPath.assign(tRow[3]);			
		}
			
		args_o.m_iNewFlag = atoi(tRow[4]);
		
		if(tRow[5] != NULL) {
			args_o.m_strDate.assign(tRow[5]);
			removeAll(args_o.m_strDate,'-');
		}
		
		other_images.push_back(args_o);
		g_objKeyFiles.push_back(args_o.m_strKeyPath);
	}//while
	mysql_free_result(pRres);
	
#endif		

	g_objFileList.clear();
	for(list<TableInfo>::iterator iter_o = other_images.begin(); iter_o != other_images.end(); iter_o++) {					
		objFileList.clear();
		for(list<TableInfo>::iterator iter_i = iqiyi_images.begin(); iter_i != iqiyi_images.end(); iter_i++) {	
			if(strcmp( (char*)iter_i->m_strKeyType.c_str(),"all") == 0 ) {
				if( ( (iter_i->m_iNewFlag == NEW_FLAG) || (iter_o->m_iNewFlag == NEW_FLAG) ) 
					&& compare_time(iter_o->m_strDate,iter_i->m_strOnlineTime) ) {
					objFileList.push_back(*iter_i);					
				}
			}
			else {		
				if( ( (iter_i->m_iNewFlag == NEW_FLAG) || (iter_o->m_iNewFlag == NEW_FLAG) ) 
					&& compare_time(iter_o->m_strDate,iter_i->m_strOnlineTime) ) {
					//objFileList.push_back(*iter_i);
					int flag = 0;
					string strSite ;
					string KeyTypeSub = iter_i->m_strKeyType;
					int pos = KeyTypeSub.find(",");
					
					while(pos != string::npos) {
						strSite = KeyTypeSub.substr(0,pos);
						KeyTypeSub = KeyTypeSub.substr(pos + 1);
						pos = KeyTypeSub.find(",");						
						if(strcmp( (char*)strSite.c_str(),(char*)iter_o->m_strSite.c_str()) == 0){
							flag = 1;
							break;
						}
						else {
							flag = 0;
						}					
					}//while
					
					if (flag == 0) {
						strSite = KeyTypeSub;
						if(strcmp( (char*)strSite.c_str(),(char*)iter_o->m_strSite.c_str()) == 0){
							flag = 1;
						}
						else {
							flag = 0;
						}
					}//if
				
					if (flag == 0) {
						objFileList.push_back(*iter_i);
					}//if
										
				}//if

			}//else
							
		}//for
		
		if(objFileList.size() > 0) {
			//g_objFileList.push_back(make_pair(*iter_i,objFileList) );	//obj->other
			g_objFileList.push_back(make_pair(*iter_o,objFileList) );	//obj->iqiyi
			cout<<"other Key->"<<iter_o->m_strKeyPath<<endl;
		}
		
	}//for

	pthread_mutex_lock(&g_mtx_lock);
	g_bReady = true;
	pthread_mutex_unlock(&g_mtx_lock);
	pthread_cond_broadcast(&g_cond_ready);
	//-------------------body--------------------
	
	cout<<"compare count ="<<g_objFileList.size()<<endl;
#if DEBUG
	printf("#%s(%d)->%s exit ! \n",__FILE__,__LINE__,__FUNCTION__);
#endif
	return ((void *)0);
}

void removeAll(string &str,char c)
{
    string::iterator new_end = remove_if(str.begin(), str.end(), bind2nd(equal_to<char>(),c));
    str.erase(new_end, str.end());
}

int compare_time(string &str1,string &str2)
{
	int res = 0;
	string str_temp1 = str1.substr(0,4);
	string str_temp2 = str2.substr(0,4);
	if(atoi(str_temp1.c_str()) > atoi(str_temp2.c_str())) {
		res = 1;
	}
	else if(atoi(str_temp1.c_str()) == atoi(str_temp2.c_str())) {
			str_temp1 = str1.substr(4,2);
			str_temp2 = str2.substr(4,2);
			if(atoi(str_temp1.c_str()) > atoi(str_temp2.c_str())) {
				res = 1;
			}
			else if(atoi(str_temp1.c_str()) == atoi(str_temp2.c_str())) {
					str_temp1 = str1.substr(6,2);
					str_temp2 = str2.substr(6,2);
					if(atoi(str_temp1.c_str()) >= atoi(str_temp2.c_str())) {
						res = 1;
					}
					else {
						res = 0;
					}
				}
				else {
					res = 0;
				}
		}
		else {
			res = 0;
		}
	
	return res;
		
}

int bitCount ( unsigned n ) {
    unsigned tmp = n - ((n >> 1) & 033333333333) - ((n >> 2) & 011111111111);
    return ( (tmp + (tmp >> 3) ) & 030707070707) % 63;
}

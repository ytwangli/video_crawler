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
#include <semaphore.h>  

#include <sstream> 
#include <algorithm> 
#include <cstdlib> 
#include <limits.h>
#include <sys/types.h>

#include "hash_lbp.h"

//for sqlite3
//#include <sqlite3.h>
#include <mysql/mysql.h>


//----------------------
#define USE_SQLITE3		0
#define USE_MYSQL		1

#define HOST_R 			"10.121.86.156"  //"sh.videomonitor.r.qiyi.db"
#define HOST_W 			"10.121.86.156"  //"sh.videomonitor.w.qiyi.db"
#define USER 			"root"           //"videomonitor"
#define PASSWD 			"iloveiqiyi"     //"evPoLol4"
#define DB 			"mysql"	         //"videomonitor"
#define PORT 			3306
//#define PORT 			8597

//-----------------------------
typedef struct _Database{	
	string m_strSite;
	string m_strImageDir;
	string m_strKeyType;
	string m_strRoi;
	string m_strKeyPath;
	int m_iNewFlag;		
}Database;

typedef struct _ThreadArgs{
	string m_strDatabase;
	string m_strTable;
	int m_ihost;
	pthread_mutex_t	m_mtx_lock;
	pthread_cond_t m_cond;
	bool m_bReady;	
	list<Database> m_lstInfo;	
}ThreadArgs;

//-------------------------------------
void* thread_getImageList(void *arg);
void* thread_makeCode(void *arg);

void formatDir(string &strDir);
int getFileList(string strDir,list<string> &pList);


//--------------------------------
char g_inPath1[PATH_MAX];
char g_inPath2[PATH_MAX];

int g_ihost = -1;
int g_threadNum = 4;
CvRect g_rectRoi = cvRect(0,0,0,0);

pthread_t tid_fileList;
pthread_t tid_makeCode[64];

string g_strKeyCodePath;	
//string g_strKeyCodePath = "/media/image/key";

ThreadArgs threadArgs;

//----------------------------main---------------------------//	
int main(int argc, char* argv[])
{		
	if(argc == 4){
		strcpy(g_inPath1,argv[1]);	//table name 
		strcpy(g_inPath2,argv[2]);	//key root path 
		g_ihost = atoi(argv[3]);	//table number 
		g_strKeyCodePath.assign(g_inPath2);
		printf("input Path1 ->%s;Path2 ->%s \n",g_inPath1,g_inPath2);
	}
	else if(argc == 5){
		strcpy(g_inPath1,argv[1]);	//table name 
		strcpy(g_inPath2,argv[2]);	//key root path 
		g_ihost = atoi(argv[3]);	//table number 
		g_threadNum = atoi(argv[4]);	//thread number
		g_strKeyCodePath.assign(g_inPath2);
		printf("input Path1 ->%s;Path2 ->%s \n",g_inPath1,g_inPath2);
	}	
	else{
		cout<<"#please input correct path ! "<<endl;
		return -1;
	}
	
	if(g_threadNum < 1){
		g_threadNum = 4;
	}
	else if(g_threadNum > 64) {
		g_threadNum = 64;
	}
	
	DIR *pRootDir = opendir( (char*)g_strKeyCodePath.c_str());  
	if(pRootDir == NULL) {		
			mkdir( (char*)g_strKeyCodePath.c_str(), S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH);	
	}
	closedir(pRootDir);
	
	while(1) {
		//------------ThreadArgs init---------------------------		
		threadArgs.m_strDatabase.assign(DB);
		threadArgs.m_strTable.assign(g_inPath1);
		threadArgs.m_ihost = g_ihost;
		threadArgs.m_bReady = false;	
		
		pthread_mutex_init(&threadArgs.m_mtx_lock,NULL);
		pthread_cond_init(&threadArgs.m_cond,NULL);		
		//sem_init(&g_sem, 0, g_threadNum);
			
		if (pthread_create(&tid_fileList, NULL, thread_getImageList, &threadArgs) != 0) {
				cout << "#create thread failed:"<< endl;
				return -1;
		}		
			
		for(int i = 0; i < g_threadNum; i++)	{
			if (pthread_create(&tid_makeCode[i], NULL, thread_makeCode, &threadArgs) != 0) {
				cout << "#create thread failed:" << i << endl;
				return -1;
			}		
		}
		
		void *threadRet;
		pthread_join(tid_fileList,&threadRet);
		
		for(int i = 0; i < g_threadNum; ++i)	{
			void *threadRet1;
			pthread_join(tid_makeCode[i],&threadRet1);
		}
		
		pthread_mutex_destroy(&threadArgs.m_mtx_lock);
		pthread_cond_destroy(&threadArgs.m_cond);
		//sem_destroy(&g_sem);
		
		cout<<"#all thread end,next loop..."<<endl;
		
		break;
		//sleep(1 * 60);
		//sleep(10 * 60);	//sleep 10 minutes
		//sleep(1 * 60 * 60);	//sleep 2 hours
	}
	
	cout<<"#all thread exit"<<endl;
	printf("#%s(%d)->%s exit ! \n",__FILE__,__LINE__,__FUNCTION__);
	return 0;
}


//--------------------------------------
void formatDir(string &strDir)
{
	if (strDir.at(strDir.length() -1) != '\\' &&
		strDir.at(strDir.length() -1) != '/')
	{
		strDir += '/';
	}
	
}

int getFileList(string strDir,list<string> &pList)
{
	DIR *pDir;
	struct dirent *pDirent;	
	string fType = ".jpg";
	int rst = -1;
	
	if(!(pDir = opendir(strDir.c_str()))) {
		cout << "#open dir failed:" << strDir << endl;
		return -1;
	}
	formatDir(strDir);	
	while((pDirent = readdir(pDir)) != NULL) {  
        if(strcmp(pDirent->d_name, ".") == 0 || strcmp(pDirent->d_name, "..") == 0) {
			continue;
		}  
  
		string strFullPath = strDir + pDirent->d_name;
		struct stat stFile;		
		if( (stat(strFullPath.c_str(), &stFile) >= 0) && (S_ISDIR(stFile.st_mode)) ) {
			//continue;
			rst &= getFileList(strFullPath,pList);			
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


void* thread_getImageList(void *arg)
{
	if (!arg) {
		printf("#%s ->arg is null ! \n",__FUNCTION__);
		return((void *)1);
	}
	//ThreadArgs
	ThreadArgs *_args = (ThreadArgs *)arg;
	
	//string &g_strDatabase=  _args->m_strDatabase;
	string &g_strTable =  _args->m_strTable;
	int ihost = _args->m_ihost;
	pthread_mutex_t &g_mtx_lock = _args->m_mtx_lock;
	pthread_cond_t &g_cond = _args->m_cond;
	bool &g_bReady = _args->m_bReady;;
	list<Database> &g_lstInfo = _args->m_lstInfo;	
			
	char szSql[1024];		
	unsigned int iRowNum = 0;
	unsigned int iFieldsNum = 0;
	
	string strTemp;
	Database databaseInfo;
		
#if USE_MYSQL
	MYSQL tMysql;
    MYSQL_RES *pRres;
    MYSQL_ROW tRow;
		
	mysql_init(&tMysql);
	//HOST_R->"sh.videomonitor.r.qiyi.db"; USER->"videomonitor"; PASSWD->"evPoLol4"; DB->"videomonitor"; PORT->8597
    if(!mysql_real_connect(&tMysql,HOST_R,USER,PASSWD,DB,PORT,NULL,0)) { 
		sleep(60);	
		if(!mysql_real_connect(&tMysql,HOST_R,USER,PASSWD,DB,PORT,NULL,0)) {       
			mysql_close(&tMysql);
			
			pthread_mutex_lock(&g_mtx_lock);
			g_bReady = true;
			pthread_mutex_unlock(&g_mtx_lock);
			pthread_cond_broadcast(&g_cond);
			
			printf("Error connecting to database:%s\n",mysql_error(&tMysql));
			return ((void *)0);
		}
    }
    	
    mysql_query(&tMysql, "SET NAMES UTF8");	
	
	//sprintf(szSql, "SELECT * FROM %s WHERE code_flag=0 AND used_flag=1 AND new_flag=1;", (char*)g_strTable.c_str() );	
	//sprintf(szSql, "SELECT site,image_dir,key_type,key_path,key_detail,new_flag FROM %s WHERE host=%d AND code_flag=0 AND used_flag=1 AND row_type!=0;", (char*)g_strTable.c_str(),ihost );
	sprintf(szSql, "SELECT site,image_dir,key_type,key_path,key_detail,new_flag FROM %s WHERE host=%d AND code_flag=0 AND used_flag=2 order by date_str desc LIMIT 16;", (char*)g_strTable.c_str(),ihost );
	mysql_query(&tMysql,szSql);	
	pRres = mysql_store_result(&tMysql);
	//pRres = mysql_use_result(&tMysql);
	iFieldsNum = mysql_num_fields(pRres);
	iRowNum = mysql_num_rows(pRres); 
	printf("%s->row:%d column=%d\n",(char*)g_strTable.c_str(),iRowNum,iFieldsNum); 
	
	while (NULL != (tRow = mysql_fetch_row(pRres)) ){
		if(tRow[0] != NULL) {
			databaseInfo.m_strSite.assign(tRow[0]);
		}
		if(tRow[1] != NULL) {
			databaseInfo.m_strImageDir.assign(tRow[1]);
		}
		if(tRow[2] != NULL) {
			databaseInfo.m_strKeyType.assign(tRow[2]);
		}				
		if(tRow[3] != NULL) {
			databaseInfo.m_strKeyPath.assign(tRow[3]);			
		}
		
		if(tRow[4] != NULL) {
			databaseInfo.m_strRoi.assign(tRow[4]);			
		}
		
		databaseInfo.m_iNewFlag = atoi(tRow[5]);
		
		//-------test------------
		//printf("%s\n",(char*)databaseInfo.m_strSite.c_str() );
		printf("%s\n",(char*)databaseInfo.m_strImageDir.c_str() );
		//printf("%s\n",(char*)databaseInfo.m_strKeyType.c_str() );
		//printf("%s\n",(char*)databaseInfo.m_strRoi.c_str() );
		//printf("%s\n",(char*)databaseInfo.m_strKeyPath.c_str() );		
		//--------------------
		
		pthread_mutex_lock(&g_mtx_lock);					
		g_lstInfo.push_back(databaseInfo);					
		pthread_mutex_unlock(&g_mtx_lock);
	
	}//while

	mysql_free_result(pRres);
	mysql_close(&tMysql);
	
#endif
	pthread_mutex_lock(&g_mtx_lock);
	g_bReady = true;
	pthread_mutex_unlock(&g_mtx_lock);
	pthread_cond_broadcast(&g_cond);
		

	printf("#%s(%d)->%s exit ! \n",__FILE__,__LINE__,__FUNCTION__);
	return ((void *)0);
}




void* thread_makeCode(void *arg)
{
	if (!arg) {
		printf("#%s ->arg is null ! \n",__FUNCTION__);
		return((void *)1);
	}
	//ThreadArgs	
	ThreadArgs *_args = (ThreadArgs *)arg;

	//string &g_strDatabase =  _args->m_strDatabase;
	string &g_strTable =  _args->m_strTable;
	int ihost = _args->m_ihost;
	pthread_mutex_t &g_mutex_lock = _args->m_mtx_lock;
	pthread_cond_t &g_cond = _args->m_cond;
	bool &g_bListEnd = _args->m_bReady;
	list<Database> &g_lstInfo = _args->m_lstInfo;
		
	FILE *fp;
	list<string> fileList;	
	Database tInfo;
	string strKeyCodePath;
	string strDirName;
	string strTemp;
	int pos = 0;
	int iRoi_x = 0;
	int iRoi_y = 0;
	int iRoi_w = 0;
	int iRoi_h = 0;
	char szSql[1024];
	
	time_t now;
	struct tm* timeinfo;	
	char* szTime = new char[100];
	
	//--------------------time-----------------------
	time(&now);
	timeinfo = localtime(&now); 
	strftime(szTime,100,"%F %T",timeinfo); 
	cout<<"#makeCodes start time->"<<szTime<<endl;
	//cout<<"#time->"<<szTime<<endl;	
	//--------------------body-----------------------
	pthread_mutex_lock(&g_mutex_lock);
	while(!g_bListEnd) {
		pthread_cond_wait(&g_cond,&g_mutex_lock);
	}
	pthread_mutex_unlock(&g_mutex_lock);

	while(g_lstInfo.size() > 0){		
		pthread_mutex_lock(&g_mutex_lock);
		tInfo = g_lstInfo.front();
		g_lstInfo.pop_front();
		pthread_mutex_unlock(&g_mutex_lock);		
		//---------------------------------------------------------
		if(tInfo.m_strImageDir.empty()) continue;
		if(tInfo.m_strSite.empty()) continue;
		strDirName.assign(tInfo.m_strImageDir);
		strKeyCodePath.assign(g_strKeyCodePath);
		
		if(tInfo.m_strSite.empty() ) {
			continue;
		}
		else {
			strKeyCodePath.append("/").append(tInfo.m_strSite);	
		}

		/*
		if( strcmp( (char*)tInfo.m_strSite.c_str(),"iqiyi") == 0 ) {
			if(tInfo.m_strKeyType.empty() ) {
				strKeyCodePath.append("/iqiyi");
			}
			else {
				//strKeyCodePath.append("/iqiyi_").append(tInfo.m_strKeyType);
				strKeyCodePath.append("/iqiyi_all");
			}			
		}
		else {
			strKeyCodePath.append("/").append(tInfo.m_strSite);
		}
		*/
		if(tInfo.m_strRoi.empty() ) {
			iRoi_x = 0;
			iRoi_y = 0;
			iRoi_w = 0;
			iRoi_h = 0;
		}
		else {			
			strTemp.assign(tInfo.m_strRoi); 
			pos = strTemp.find_first_of(",");
			iRoi_x = atoi( (char*)strTemp.substr(0,pos).c_str() );
			strTemp.assign(strTemp.substr(pos+1));
			pos = strTemp.find_first_of(",");
			iRoi_y = atoi( (char*)strTemp.substr(0,pos).c_str() );
			strTemp.assign(strTemp.substr(pos+1));
			pos = strTemp.find_first_of(",");
			iRoi_w = atoi( (char*)strTemp.substr(0,pos).c_str() );
			strTemp.assign(strTemp.substr(pos+1));
			iRoi_h = atoi( (char*)strTemp.c_str() );
		}
		g_rectRoi = cvRect(iRoi_x,iRoi_y,iRoi_w,iRoi_h);	
		//cout<<"#roi->x ="<<g_rectRoi.x<<";roi->y ="<<g_rectRoi.y<<"#roi->width ="<<g_rectRoi.width<<"#roi->height ="<<g_rectRoi.height<<endl;
		//for Adaptive
		DIR *pDir = opendir( (char*)strKeyCodePath.c_str());  
		if(pDir == NULL) {		
			mkdir( (char*)strKeyCodePath.c_str(), S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH);	
		}
		closedir(pDir);
		
		pos = strDirName.find_last_of("/");
		string strDirTmp1 = strDirName.substr(pos+1);		
		string codeFile = strKeyCodePath + "/" + strDirTmp1 + ".key";		
	
		if( (access(codeFile.c_str(),0) == 0)) {		
			cout<<"#key file is exist->"<<codeFile<<endl;
#if 0
			MYSQL tMysql;		
			mysql_init(&tMysql);
			//HOST_W->"sh.videomonitor.w.qiyi.db"; USER->"videomonitor"; PASSWD->"evPoLol4"; DB->"videomonitor"; PORT->8597
			if(!mysql_real_connect(&tMysql,HOST_W,USER,PASSWD,DB,PORT,NULL,0)) {       
				mysql_close(&tMysql);				
				printf("Error connecting to database:%s\n",mysql_error(&tMysql));
				delete[] szTime;
				return ((void *)0);
			}    	
			mysql_query(&tMysql, "SET NAMES UTF8");	
			sprintf(szSql, "UPDATE %s SET key_path='%s', code_flag=%d WHERE host=%d AND image_dir='%s' AND key_type='%s';", 
								(char*)g_strTable.c_str(), (char*)codeFile.c_str(),1,ihost,(char*)strDirName.c_str(), (char*)tInfo.m_strKeyType.c_str() );
			mysql_query(&tMysql,szSql);	
			mysql_close(&tMysql);	
#endif
			continue;
		}
		
		if(getFileList(strDirName,fileList) != 0){
			printf("#no files break while loop;%s(%d)->%s! file->%s \n",__FILE__,__LINE__,__FUNCTION__,(char*)strDirName.c_str());
			continue;
		}
		
		int hCode[2] = {0};
		float hist[59] = {0};
		stringstream  sstr;
		fp = fopen(codeFile.c_str(),"w");
		while(fileList.size() > 0){
			string imgFile = fileList.front();
			fileList.pop_front();
			string code;
			
			memset(hCode,0,sizeof(int)*2);
			pHashCode((char*)imgFile.c_str(), hCode,g_rectRoi);

			unsigned count = 0;
			for(int i = 0; i < 2; i++){
				int temp = hCode[i];
				for(int j = 0; j < 32; j++) {
					if (temp & 0x80000000) count++;
					temp = temp << 1;
				}
			}
			sstr<<count;
			code.append(sstr.str()).append(",");			
			sstr.clear();
			sstr.str("");
			
			for(int i = 0; i < 2; i++){
				sstr<<hCode[i];
				code.append(sstr.str()).append(",");			
				sstr.clear();
				sstr.str("");
			}
			
			memset(hist,0,sizeof(float)*59);
			getLbpHist((char*)imgFile.c_str(),g_rectRoi,hist,1);
			for(int i = 0; i < 59; i++){
				sstr<<hist[i];
				code.append(sstr.str()).append(",");			
				sstr.clear();
				sstr.str("");
			}
			code.append(imgFile).append("\n");
			fwrite((char*)code.c_str(),code.size(),1,fp);
		}
		fclose(fp);
		
		time(&now);
		timeinfo = localtime(&now); 
		strftime(szTime,100,"%F %T",timeinfo); 
		
		cout<<"time->"<<szTime<<endl;		
		cout<<"#make a key file ok->"<<codeFile<<endl;

#if USE_MYSQL
		MYSQL tMysql;
		//MYSQL_RES *pRres;
		//MYSQL_ROW tRow;
			
		mysql_init(&tMysql);
		//HOST_W->"sh.videomonitor.w.qiyi.db"; USER->"videomonitor"; PASSWD->"evPoLol4"; DB->"video_data"; PORT->8597
		if(!mysql_real_connect(&tMysql,HOST_W,USER,PASSWD,DB,PORT,NULL,0)) { 
			sleep(60);
			if(!mysql_real_connect(&tMysql,HOST_W,USER,PASSWD,DB,PORT,NULL,0)) {       
				mysql_close(&tMysql);				
				printf("Error connecting to database:%s\n",mysql_error(&tMysql));
				delete[] szTime;
				return ((void *)0);
			}
		}
			
		mysql_query(&tMysql, "SET NAMES UTF8");
			
		sprintf(szSql, "UPDATE %s SET key_path='%s',code_flag=%d,update_date='%s' WHERE host=%d AND image_dir='%s' AND key_type='%s';", 
							(char*)g_strTable.c_str(), (char*)codeFile.c_str(),1,szTime,ihost,(char*)strDirName.c_str(), (char*)tInfo.m_strKeyType.c_str() );
		mysql_query(&tMysql,szSql);
		
		//mysql_free_result(pRres);
		mysql_close(&tMysql);
	
#endif		
		cout<<"#database update key_path->"<<codeFile<<endl;
		
	}//while
	
	printf("#%s(%d)->%s exit ! \n",__FILE__,__LINE__,__FUNCTION__);
	
	delete[] szTime;
	return ((void *) 0);
}



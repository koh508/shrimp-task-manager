
import csv
import io

def parse_contacts(file_content):
    contacts = []
    # Use StringIO to treat the string content as a file
    f = io.StringIO(file_content)
    reader = csv.reader(f)
    header = next(reader)  # Skip header

    for row in reader:
        if not row:
            continue

        name = ""
        title = ""
        phone = ""

        # Try to get name from First Name (index 0) or a combination of names
        if row[0]: # First Name
            name = row[0]
        elif row[2]: # Last Name
            name = row[2]
        elif row[8]: # Nickname
            name = row[8]
        elif row[10]: # Organization Name
            name = row[10]
        elif row[11]: # Organization Title
            name = row[11]

        # Try to get title from Organization Title (index 11)
        if row[11]:
            title = row[11]
        elif row[10] and not name: # If name is empty, use organization name as title if available
            title = row[10]

        # Get phone number from Phone 1 - Value (index 18)
        if len(row) > 18 and row[18]:
            phone = row[18]

        if name or title or phone: # Only add if some information is present
            contacts.append({"name": name.strip(), "title": title.strip(), "phone": phone.strip()})

    return contacts


if __name__ == "__main__":
    # This part will be executed when the script is called directly
    # In the actual agent flow, the content will be passed as an argument
    # For testing, you can put sample data here
    sample_file_content = """First Name,Middle Name,Last Name,Phonetic First Name,Phonetic Middle Name,Phonetic Last Name,Name Prefix,Name Suffix,Nickname,File As,Organization Name,Organization Title,Organization Department,Birthday,Notes,Photo,Labels,Phone 1 - Label,Phone 1 - Value
,,,,,,,,,,,,,,,,* myContacts,Mobile,010-9444-2328
,,,,,,,,,,,,,,,,* myContacts,Mobile,010-9599-6073
5g문섬중계기공사 (11.3),,,,,,,,,,,,,,,,* myContacts,Mobile,01079424773
5톤 카고 크레인,,,,,,,,,,,,,,,,* myContacts,Mobile,01050901551
amy,,,,,,,,,,,,,,,,* myContacts,Mobile,01076435169
a조 강지훈사원,,,,,,,,,,,,,,,,* myContacts,Mobile,01099390993
B조 박유현대리 조장,,,,,,,,,,,,,,,,* myContacts,Mobile,01086648982
cctv 업체,,,,,,,,,,,,,,,,* myContacts,Mobile,01056489656
c조 김승현 조장,,,,,,,,,,,,,,,,* myContacts,Mobile,01029305462
D조 강진석주임,,,,,,,,,,,,,,,,* myContacts,Mobile,01072385590
d조 배종현주임님,,,,,,,,,,,,,,,,* myContacts,Mobile,01090951585
d조 하현씨,,,,,,,,,,,,,,,,* myContacts,Mobile,01067388520
ks건재 직원분,,,,,,,,,,,,,,,,* myContacts,Mobile,01029253461 ::: 01062956252
ks직원 3,,,,,,,,,,,,,,,,* myContacts,Mobile,01089715341
lg에어컨 기사 세정의 건,,,,,,,,,,,,,,,,* myContacts,Mobile,01023597018
MIT 손동원 과장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01076542759
pcb업체,,,,,,,,,,,,,,,,* myContacts,Mobile,01020318711
,,Rf.ace 고객센터,,,,,,,,,,,,,,* myContacts,Mobile,02-2083-8336
uv램프 업체,,,,,,,,,,,,,,,,* myContacts,Mobile,01041815801
가스검침원,,,,,,,,,,,,,,,,* myContacts,Mobile,01097173439
이건열차장,,가스안전공사,,,,,,,,,,,,,,Restored from Blackberry - BBF100-6 ::: * myContacts,,01056936655
강동주 기사(자원환경순환센터),,,,,,,,,,,,,,,,* myContacts,Mobile,01041930036
배근계장님(LSS),,강,,,,,,,,,,,,,,* myContacts,,01063001021
강배근계장님(시설),,,,,,,,,,,,,,,,Restored from Blackberry - BBF100-6 ::: * myContacts,,01063001021
강병철형님(성일로스타),,,,,,,,,,,,,,,,* myContacts,Home,‎010-6473-0434
강석빈,,,,,,,,,,,,,,,,* myContacts,Mobile,01041718785
강석우 차장님(명진기업),,,,,,,,,,,,,,,,* myContacts,Mobile,01041034487
강슬기님,,,,,,,,,,,,,,,,* myContacts,Mobile,01023493475
강원국 선배(포유류),,,,,,,,,,,,,,,,* myContacts,Mobile,01055332671
강진석 d조 크레인,,,,,,,,,,,,,,,,* myContacts,Mobile,01020484164
경준(콘크리트노가다),,,,,,,,,,,,,,,,* myContacts,Mobile,010-2892-5578
계량ㄷ 고상범 주임,,,,,,,,,,,,,,,,* myContacts,Mobile,01099849797
계량대 김예진 사원(자원순환센터),,,,,,,,,,,,,,,,* myContacts,Mobile,01027304791
고상식 차장님(자원순환센터),,,,,,,,,,,,,,,,* myContacts,Mobile,01027282853
고상식 차장님(자원환경순환센터),,,,,,,,,,,,,,,,* myContacts,Mobile,01027282863
,,고석준(둘리),,,,,,,,,,,,,,* myContacts,Mobile,010-7563-9408
고신화,,,,,,,,,,,,,,,,* myContacts,Mobile,01037320427
,,고용돈(사촌형),,,,,,,,,,,,,,* myContacts,Mobile,010-4721-2522
,,고용석,,,,,,,,,,,,,,* myContacts,Mobile,010-4704-8060
고용준 기사,,,,,,,,,,,,,,,,* myContacts,Mobile,01048147944
고용진(사촌),,,,,,,,,,,,,,,,* myContacts,Mobile,01043328060
고형창과장님 운영 D조 조장(자원),,,,,,,,,,,,,,,,* myContacts,,
고형창과장님(D조 조장),,,,,,,,,,,,,,,,* myContacts,Mobile,01029259999
,,고희웅(영),,,,,,,,,,,,,,* myContacts,Mobile,+82 10-8008-0560
성식형,,공,,,,,,,,,,,,,,* myContacts,Mobile,010-5554-9950
관리팀 팀장 강문석 부장(자원순환센터),,,,,,,,,,,,,,,,* myContacts,Mobile,01066204043
광용형님(전기기술자),,,,,,,,,,,,,,,,* myContacts,Mobile,01050301992
광컨버터,,,,,,,,,,,,,,,,* myContacts,,0647268046
휘,,광,,,,,,,,,,,,,,* myContacts,Mobile,010-9799-0514
일상회(알곤),,국,,,,,,,,,,,,,,* myContacts,Mobile,031-563-2407
,,굿타이어,,,,,,,,,,,,,,* myContacts,Mobile,010-2649-9887
극동씰테크,,,,,,,,,,,,,,,,* myContacts,Mobile,01038986282
금남 남용진부장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01096604635
금남 유동근 과장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01031224420
금남플랜트 장정훈과장,,,,,,,,,,,,,,,,* myContacts,Mobile,01042100972
기장엔지니어링 에너지관리 저가해줌,,,,,,,,,,,,,,,,* myContacts,Mobile,+82 10-4742-8609
기획총무 강선철(전임) (자원순환센터),,,,,,,,,,,,,,,,* myContacts,,
김경림,,,,,,,,,,,,,,,,* myContacts,Mobile,01034708307
김경하과장님 운영 A조 조장(자원),,,,,,,,,,,,,,,,* myContacts,Mobile,01087240927
김과장님(성일로스타),,,,,,,,,,,,,,,,* myContacts,Mobile,010-4994-4190
김광복과장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01056491258
김광중차장님 에어로,,,,,,,,,,,,,,,,* myContacts,Mobile,01040785156
,,김나림,,,,,,,,,,,,,,* myContacts,Mobile,010-8293-9334
김동균팀장님(페인트),,,,,,,,,,,,,,,,* myContacts,Mobile,01041681644
,,김동완팀장님,,,,,,,,,,,,,,* myContacts,Mobile,010-2657-3290
동환주임(한화),,김,,,,,,,,,,,,,,Restored from Blackberry - BBF100-6 ::: * myContacts,,01062331096
,,김민석주임(어류파트),,,,,,,,,,,,,,* myContacts,Mobile,010-4701-9071
김민정선배님(포유류),,,,,,,,,,,,,,,,* myContacts,Mobile,01029606429
병섭계장님(한화),,김,,,,,,,,,,,,,,* myContacts,,01092288009
병섭대리님(LSS)(파트장),,김,,,,,,,,,,,,,,Restored from Blackberry - BBF100-6 ::: * myContacts,,01092288009
김병수이사님,,,,,,,,,,,,,,,,* myContacts,Mobile,01057553824
솔이_만나,,김,,,,,,,,,,,,,,* myContacts,Other,010-4100-3698
영훈,,김,,,,,,,,,,,,,,* myContacts,Mobile,010-5103-7485
요한,,김,,,,,,,,,,,,,,* myContacts,Mobile,010-2422-0768
우주선배,,김,,,,,,,,,,,,,,* myContacts,Mobile,+821090644915
김응복주임,,,,,,,,,,,,,,,,* myContacts,Mobile,01066838345
이준형,,김,,,,,,,,,,,,,,* myContacts,Mobile,010-4110-4363
김정훈 사원,,,,,,,,,,,,,,,,* myContacts,Mobile,01096902948
종욱,,김,,,,,,,,,,,,,,ICE ::: * myContacts,Mobile,010-9611-0276
김진호 선배 (포유류파트),,,,,,,,,,,,,,,,* myContacts,Mobile,01083771591
,,김해강주임,,,,,,,,,,,,,,* myContacts,Mobile,010-5721-1233
김현성,,,,,,,,,,,,,,,,* myContacts,Mobile,01036193104
김현우선임(뻥크린),,,,,,,,,,,,,,,,* myContacts,Mobile,01026732643
,,김혜경누나,,,,,,,,,,,,,,* myContacts,Mobile,010-9181-5199
대표,,김호진(상상이노베이션) 고보라이트,,,,,,,,,,,,,,* myContacts,Other,+82 10-6243-8031
김호현 주임(한화),,,,,,,,,,,,,,,,* myContacts,Mobile,01050081489
조명감독eos,,남수정(오션아레나),,,,,,,,,,,,,,* myContacts,Other,010-8939-6454
냉각탑 공사 소장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01042312909
동탐진에이알박경우,,냉,,,,,,,,,,,,,,* myContacts,Other,010-5273-4973
노주임님(제주환경자원순환센터),,,,,,,,,,,,,,,,* myContacts,Mobile,01099249615
누구니,,,,,,,,,,,,,,,,* myContacts,Mobile,01024991552
,,누구니,,,,,,,,,,,,,,* myContacts,Mobile,010-2222-5222
,,누구니2,,,,,,,,,,,,,,* myContacts,Mobile,010-3691-1122
나,,누,,,,,,,,,,,,,,* myContacts,Mobile,010-4451-6451
다복식당,,,,,,,,,,,,,,,,* myContacts,,0647823230
다이아누님,,,,,,,,,,,,,,,,* myContacts,Mobile,01087987917
,,달달누나,,,,,,,,,,,,,,* myContacts,Mobile,010-4828-4862
,,대동철공소,,,,,,,,,,,,,,* myContacts,Mobile,051-413-7001
존공조(메인수조덕트공사),,더,,,,,,,,,,,,,,* myContacts,Mobile,010-4181-7162
덕트시공업체(이수진팀장),,,,,,,,,,,,,,,,* myContacts,Mobile,01034071182
동복리 사무국장,,,,,,,,,,,,,,,,* myContacts,Mobile,01051312072
동양 작업반장,,,,,,,,,,,,,,,,* myContacts,Mobile,01087098232
두성기업 김성철대표님,,,,,,,,,,,,,,,,* myContacts,Mobile,01088927034
디씨660 서비스센터,,,,,,,,,,,,,,,,* myContacts,,07088710968
라인닥트 경리,,,,,,,,,,,,,,,,* myContacts,Mobile,01049330628
롯데렌터카 장기 계약,,,,,,,,,,,,,,,,* myContacts,Mobile,01092804615
,,롯데택배차량(운적석 오른쪽 찍어버림),,,,,,,,,,,,,,* myContacts,Mobile,010-3639-0461
리박 김성연대리,,,,,,,,,,,,,,,,* myContacts,Mobile,01044411825
,,리소텍(실내공기질업체),,,,,,,,,,,,,,* myContacts,Mobile,1661-0203
맑은누리 이치봉 대표,,,,,,,,,,,,,,,,* myContacts,Mobile,01063995203
맑은누리 작업자,,,,,,,,,,,,,,,,* myContacts,Mobile,01033821858
스맨,,맥,,,,,,,,,,,,,,* myContacts,Mobile,010-7632-4958
메인수조 신한은행 설비팀,,,,,,,,,,,,,,,,* myContacts,Mobile,01046507141
량경비쌤,,명,,,,,,,,,,,,,,* myContacts,Mobile,010-7773-0469
,,명성자동문 상무님,,,,,,,,,,,,,,* myContacts,Mobile,010-6690-0985
라룡,,문,,,,,,,,,,,,,,* myContacts,Mobile,010-4005-9377
,,뭔데형,,,,,,,,,,,,,,* myContacts,Mobile,010-4256-7982
미우라보일라 검사원,,,,,,,,,,,,,,,,* myContacts,Mobile,01098130148
미우라보일러 고영재사원,,,,,,,,,,,,,,,,* myContacts,Mobile,01098130363
수홍,,민,,,,,,,,,,,,,,* myContacts,Mobile,010-8876-9849
바로씨앤에스 김영학과장,,,,,,,,,,,,,,,,* myContacts,Mobile,01056210143
박동우 인테리어 팀장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01025239393
박민성주임님(한화),,,,,,,,,,,,,,,,* myContacts,Mobile,01094578939
,,박세영(박우니),,,,,,,,,,,,,,* myContacts,Mobile,010-4535-1106
박정철(쎄라텍코)안전변,,,,,,,,,,,,,,,,* myContacts,Mobile,01089252888
박정훈 주임 (자원순환센터),,,,,,,,,,,,,,,,* myContacts,Mobile,01089954331
현선,,박,,,,,,,,,,,,,,* myContacts,Mobile,010-2310-2394
,,박형준 시닙,,,,,,,,,,,,,,* myContacts,Mobile,010-2736-2550
반입장 박재훈 주임,,,,,,,,,,,,,,,,* myContacts,Mobile,01036946491
반입장 이성삼 주임,,,,,,,,,,,,,,,,* myContacts,Mobile,01094580595
반입장 장윤호 주임,,,,,,,,,,,,,,,,* myContacts,Mobile,01098407915
,,방재실1,,,,,,,,,,,,,,* myContacts,Mobile,064-780-0946
,,방재실2,,,,,,,,,,,,,,* myContacts,Mobile,064-780-0944
,,방재실에어컨 실외기기사님,,,,,,,,,,,,,,* myContacts,Mobile,010-2641-7954
,,방지턱 공사 사장님,,,,,,,,,,,,,,* myContacts,Mobile,010-3697-6149
범양냉방제주 서귀대리점,,,,,,,,,,,,,,,,* myContacts,,0647620182
,,벤쯔 돌I,,,,,,,,,,,,,,* myContacts,Mobile,010-2983-2678
변승원,,,,,,,,,,,,,,,,* myContacts,Mobile,01035422538
보광전업사 송태진 사장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01027999572
보광전업사 아드님,,,,,,,,,,,,,,,,* myContacts,Mobile,01074449572
보험(아버지친구),,,,,,,,,,,,,,,,* myContacts,Mobile,01055679311
본사 전금희 차장님,,,,,,,,,,,,,,,,* myContacts,,0314102313
부사장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01080241498
부천기업 이춘건 과장,,,,,,,,,,,,,,,,* myContacts,Mobile,01066536010
부천기업 프로그램머,,,,,,,,,,,,,,,,* myContacts,Mobile,01021027285
빠우반장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01037816933
,,산도롱,,,,,,,,,,,,,,* myContacts,Mobile,010-7503-6491
살수차 부성민님,,,,,,,,,,,,,,,,* myContacts,Mobile,01028962646
삼다이엔디 에어컨(고정식),,,,,,,,,,,,,,,,* myContacts,Mobile,01093651590
삼다이엔지,,,,,,,,,,,,,,,,* myContacts,Mobile,01020026759
삼다이엔지 대리,,,,,,,,,,,,,,,,* myContacts,Mobile,01025541503
삼덕여과산업 구성준 과장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01098030684
삼양stn 5G 공사팀11.3 장석보 팀장,,,,,,,,,,,,,,,,* myContacts,Mobile,01086621565
삼일승강기,,,,,,,,,,,,,,,,* myContacts,,0647268869
,,삼일승강기,,,,,,,,,,,,,,* myContacts,Mobile,010-6690-7959
삼일승강기 ㄱ점검자,,,,,,,,,,,,,,,,* myContacts,Mobile,01051375520
삼평사장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01036991671
삼흥베어링,,,,,,,,,,,,,,,,* myContacts,,0647536735
석형님,,상,,,,,,,,,,,,,,* myContacts,Home,‎010-4613-1292
,,상준이형,,,,,,,,,,,,,,* myContacts,Mobile,010-4848-6515
샤갸,,,,,,,,,,,,,,,,* myContacts,Mobile,01028034112
서우성 기사(자원환경순환센터),,,,,,,,,,,,,,,,* myContacts,Mobile,01071316163
서의봉(환경자원순환센터),,,,,,,,,,,,,,,,* myContacts,Mobile,01029112403
,,석원,,,,,,,,,,,,,,* myContacts,Mobile,010-3321-9806
설택 김홍선차장 풍력발전기,,,,,,,,,,,,,,,,* myContacts,Mobile,01091141205
,,성호환경(폐기물),,,,,,,,,,,,,,* myContacts,Mobile,010-733-5181
세라텍코 도기덕대리,,,,,,,,,,,,,,,,* myContacts,Mobile,01055737033
세림물산,,,,,,,,,,,,,,,,* myContacts,Mobile,01021236330
세콤 24,,,,,,,,,,,,,,,,* myContacts,Mobile,01092053168
,,손날두형님,,,,,,,,,,,,,,* myContacts,Mobile,010-2548-0461
송동준선생님(야간당직자),,,,,,,,,,,,,,,,* myContacts,Mobile,01029949544
송진석님(가소작가),,,,,,,,,,,,,,,,* myContacts,Mobile,01075745946
송훈혁과장님(한화LSS),,,,,,,,,,,,,,,,Restored from Blackberry - BBF100-6 ::: * myContacts,,01026365697
수정케미칼 사장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01037102213
수진,,,,,,,,,,,,,,,,* myContacts,Mobile,010-2514-4569
순욱주임님,,,,,,,,,,,,,,,,* myContacts,Mobile,01064264561
베리님,,슈,,,,,,,,,,,,,,* myContacts,Mobile,010-9219-0889
신성 이석희 부장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01098230660
신일 이기승소장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01063580892
신일 이수웅 대표님,,,,,,,,,,,,,,,,* myContacts,Mobile,01050228947
신일 이수홍 차장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01027910830
신일 총무님 새번호,,,,,,,,,,,,,,,,* myContacts,Mobile,01031250840
신일 허현일 비계팀 반장,,,,,,,,,,,,,,,,* myContacts,Mobile,01040038956
신한공조 기술자,,,,,,,,,,,,,,,,* myContacts,Mobile,01037846905
신한상부장님(명진),,,,,,,,,,,,,,,,* myContacts,Mobile,01093942233
신현호,,,,,,,,,,,,,,,,* myContacts,Mobile,01051505635
신화건설 김양국반장,,,,,,,,,,,,,,,,* myContacts,Mobile,01087513291
재훈,,심,,,,,,,,,,,,,,* myContacts,Mobile,010-4597-5932
쌍용기계,,,,,,,,,,,,,,,,* myContacts,,0647224926
쌍용스텐 김호과장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01042229622
쎄라테고 송현덕부장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01086500570
,,아버지,,,,,,,,,,,,,,ICE ::: * myContacts,Mobile,+82 10-4946-2138
,,안예인주임(포유류파트),,,,,,,,,,,,,,* myContacts,Mobile,010-4399-8910
시온님,,알,,,,,,,,,,,,,,* myContacts,Mobile,010-4847-1592
양두경 전기 (자원순환센터),,,,,,,,,,,,,,,,* myContacts,,
양두경 주임 (자원순환센터),,,,,,,,,,,,,,,,* myContacts,Mobile,010-2699-7971
씨,,양,,,,,,,,,,,,,,* myContacts,Mobile,010-9104-2792
양원철반장님 (페인트공사),,,,,,,,,,,,,,,,* myContacts,Mobile,01091383104
양원호,,,,,,,,,,,,,,,,* myContacts,Mobile,01093975281
양유신 주임 (자원순환센터),,,,,,,,,,,,,,,,* myContacts,Mobile,01036931463
양재욱주임,,,,,,,,,,,,,,,,* myContacts,Mobile,01065052762
양지은,,,,,,,,,,,,,,,,* myContacts,Mobile,01023494880
양태웅기사,,,,,,,,,,,,,,,,* myContacts,Mobile,01040902108
어류파트 김희재(신입),,,,,,,,,,,,,,,,* myContacts,Mobile,01092953751
류파트채정희파트장님,,어,,,,,,,,,,,,,,Restored from Blackberry - BBF100-6 ::: * myContacts,,01039973130
머니,,어,,,,,,,,,,,,,,* myContacts,Mobile,010-2963-0616
에너지공사,,,,,,,,,,,,,,,,* myContacts,,0216701756
에너지서베이,,,,,,,,,,,,,,,,* myContacts,,0220683517
,,에너지진단 아텍 전무,,,,,,,,,,,,,,* myContacts,Mobile,+82 10-5539-3569
신영길이사님,,에너지진단(씨엔에스시절),,,,,,,,,,,,,,* myContacts,Mobile,010-2686-2583
,,에너지진단업체2,,,,,,,,,,,,,,* myContacts,Mobile,+82 10-2560-6962
,,에너지프로 예병진 차장(에너지진단),,,,,,,,,,,,,,* myContacts,Mobile,010-5717-4770
에스원 정영운 기술팀장,,,,,,,,,,,,,,,,* myContacts,Mobile,01025063471
에스텍 창원 김홍수소장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01064159301
에스텍 창원 폐수팀장 이형욱,,,,,,,,,,,,,,,,* myContacts,Mobile,01064922204
에스텍 창원공무 이동락,,,,,,,,,,,,,,,,* myContacts,Mobile,01064304726
에스텍코리아 정택이사님,,,,,,,,,,,,,,,,* myContacts,Mobile,01063139457
,,에스텍코리아(인사담당자),,,,,,,,,,,,,,* myContacts,Mobile,+82 10-4301-0796
에어월드,,,,,,,,,,,,,,,,* myContacts,Mobile,01030984569
에이피 FCU업체 공대성과장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01034494892
엘쥐중계기 김완석부장,,,,,,,,,,,,,,,,* myContacts,Mobile,010-9633-3749
엘지 강태호 사장님 (상무님 친구분),,,,,,,,,,,,,,,,* myContacts,Mobile,01087373781
엘지 서비스기사 소각동 관리동 에어컨공사,,,,,,,,,,,,,,,,* myContacts,Mobile,01043540801
예인박종현부장,,,,,,,,,,,,,,,,* myContacts,Mobile,01053360552
오도언,,,,,,,,,,,,,,,,* myContacts,Mobile,010-9938-1278
오름형님,,,,,,,,,,,,,,,,* myContacts,Mobile,01074439299
오석송과장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01034757410
오월님,,,,,,,,,,,,,,,,* myContacts,Mobile,01085707872
재득계장님(LSS),,오,,,,,,,,,,,,,,Restored from Blackberry - BBF100-6 ::: * myContacts,,01044226018
,,용용형,,,,,,,,,,,,,,* myContacts,Mobile,010-3220-3494
우진라페 손창식소장,,,,,,,,,,,,,,,,* myContacts,Mobile,01052955166
우채송 운영팀선배,,,,,,,,,,,,,,,,* myContacts,Mobile,01088748242
원공조 서류담당,,,,,,,,,,,,,,,,* myContacts,Mobile,01063853839
원공조 여자사장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01084190001
원공조 점검구 인테리어팀 (민범),,,,,,,,,,,,,,,,* myContacts,Mobile,01026927698
윌로대리점 강현택 소장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01036937273
,,유디엘레베이터,,,,,,,,,,,,,,* myContacts,Mobile,064-723-6566
유혜진,,,,,,,,,,,,,,,,* myContacts,Mobile,01051887535
윤균성 tms,,,,,,,,,,,,,,,,* myContacts,Mobile,01062126191
윤하경님,,,,,,,,,,,,,,,,* myContacts,Mobile,01066151890
은하기업 이사님,,,,,,,,,,,,,,,,* myContacts,Mobile,+821086642507
은혜,,,,,,,,,,,,,,,,* myContacts,Mobile,010-6711-1117
이규식 주임 (제주환경자원순환센터),,,,,,,,,,,,,,,,* myContacts,Mobile,01029641209
이병규과장님 운영 C조 조장(자원),,,,,,,,,,,,,,,,* myContacts,Mobile,01071778385
상호(한독카리스),,이,,,,,,,,,,,,,,* myContacts,Other,010-4414-0841
이수빈 주임(제주환경자원순환센터),,,,,,,,,,,,,,,,* myContacts,Mobile,01052342376
이승호기사,,,,,,,,,,,,,,,,* myContacts,Mobile,01076795445
영석주임(한화),,이,,,,,,,,,,,,,,Restored from Blackberry - BBF100-6 ::: * myContacts,,01083258852
이윤석과장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01020821031
이재광님,,,,,,,,,,,,,,,,* myContacts,Mobile,01097345628
,,이재만(팬더),,,,,,,,,,,,,,* myContacts,Mobile,+82 10-4829-4214
재은,,이,,,,,,라쓰님,,,,,,,,* myContacts,Mobile,010-6777-1005
이정철 차장님(에스텍코리아),,,,,,,,,,,,,,,,* myContacts,Mobile,01082164860
이종철 (원공조시스템),,,,,,,,,,,,,,,,* myContacts,Mobile,01064297789
이주연주임(명진),,,,,,,,,,,,,,,,* myContacts,Mobile,01076659459
이태걸 주임(자원환경순환센터),,,,,,,,,,,,,,,,* myContacts,Mobile,01090438808
이토 미에,,,,,,,,,,,,,,,,* myContacts,Mobile,01080136792
이학영 상무님 (에스텍코리아),,,,,,,,,,,,,,,,* myContacts,Mobile,01023016547
이호문주임,,,,,,,,,,,,,,,,* myContacts,Mobile,01048025780
,,일출냉열 오창배사장님,,,,,,,,,,,,,,* myContacts,Mobile,010-3696-6563
음님,,있,,,,,,,,,,,,,,* myContacts,Mobile,+82 10-5047-2313
작은아버지,,,,,,,,,,,,,,,,* myContacts,Mobile,01035699345
장구공사 디씨660,,,,,,,,,,,,,,,,* myContacts,,028960909
장완건설 오광진 반장님 (도장),,,,,,,,,,,,,,,,* myContacts,Mobile,01092711301
장윤호(장차님 아들),,,,,,,,,,,,,,,,* myContacts,Mobile,01058320779
장은성사원 c조,,,,,,,,,,,,,,,,* myContacts,Mobile,01051186573
장정수차장님 (정비팀),,,,,,,,,,,,,,,,* myContacts,Mobile,01084660779 ::: 01084660779
현수공장장님,,장,,,,,,,,,,,,,,* myContacts,Mobile,010-3332-1818
전지민선배(어류파트),,,,,,,,,,,,,,,,* myContacts,Mobile,01040097394
정과장님(에스텍코리아),,,,,,,,,,,,,,,,* myContacts,Mobile,01030410200
삼성보험사,,정명애,,,,,,,,,,,,,,* myContacts,Home,‎010-8861-5326
정미선주임님(한화),,,,,,,,,,,,,,,,* myContacts,Mobile,01093764206
정민우 선배(포유류),,,,,,,,,,,,,,,,* myContacts,Mobile,01024209559
,,정영현주임(어류파트),,,,,,,,,,,,,,* myContacts,Mobile,010-8249-7520
정욱(고은희 외삼촌),,,,,,,,,,,,,,,,* myContacts,Mobile,01076200164
윤성(야간당직자),,정,,,,,,,,,,,,,,Restored from Blackberry - BBF100-6 ::: * myContacts,,01066073924
정의현대리님(에스텍),,,,,,,,,,,,,,,,* myContacts,Mobile,01025186105
,,정장호이사님(명진),,,,,,,,,,,,,,* myContacts,Mobile,010-3682-6232
제이텍 강찬길 대표(열화상카메라),,,,,,,,,,,,,,,,* myContacts,Mobile,01030961171
일자동문,,제,,,,,,,,,,,,,,* myContacts,Other,010-2840-8858
제주환경개발,,,,,,,,,,,,,,,,* myContacts,Mobile,01047732872
제주환경자원순환센터 C조 조주혁사원,,,,,,,,,,,,,,,,* myContacts,Mobile,010-4170-1108
제주환경자원순환센터 김동수기사님,,,,,,,,,,,,,,,,* myContacts,Mobile,01067989119
제주환경자원순환센터 정비팀 이동엽대리님,,,,,,,,,,,,,,,,* myContacts,Mobile,01021635560
조선내화 임종근 부장,,,,,,,,,,,,,,,,* myContacts,Mobile,01038680924
부파트장님(포유류),,조재현,,,,,,,,,,,,,,Restored from Blackberry - BBF100-6 ::: * myContacts,,01077368422
조화경 주임님(자원순환센터),,,,,,,,,,,,,,,,* myContacts,Mobile,01088337193
주복택차장님(한화),,,,,,,,,,,,,,,,* myContacts,Mobile,01064236729
,,주식회사 제주ENG,,,,,,,,,,,,,,* myContacts,Mobile,064-712-8880
,,주식회사 제주이엔지(폐소화기)담당자,,,,,,,,,,,,,,* myContacts,Mobile,+82 10-9515-8250
주인정보시스템,,,,,,,,,,,,,,,,* myContacts,,0220540050
주편동 소장,,,,,,,,,,,,,,,,* myContacts,Mobile,01064385129
주편동 야간기사,,,,,,,,,,,,,,,,* myContacts,Mobile,01041841425
주편동 양현식반장,,,,,,,,,,,,,,,,* myContacts,Mobile,01077396142
준범씨,,,,,,,,,,,,,,,,* myContacts,Mobile,01080099135
진형우 전임,,,,,,,,,,,,,,,,* myContacts,Mobile,01072490904
,,집주인 이도이동,,,,,,,,,,,,,,* myContacts,Mobile,+82 10-6630-1461
주인(김용수),,집,,,,,,,,,,,,,,Restored from Blackberry - BBF100-6 ::: * myContacts,,01041581710
차예진 선배(어류 파트),,,,,,,,,,,,,,,,* myContacts,Mobile,01049819464
사무료급식소,,천,,,,,,,,,,,,,,* myContacts,Mobile,+82 10-7455-0031
청우 강명오 반장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01031816609
청우 김종근 반장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01041690067
청우 이용선반장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01037177186
청우영업반장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01062484437
최동주씨,,,,,,,,,,,,,,,,* myContacts,Mobile,01040844810
최부장(성일로스타),,,,,,,,,,,,,,,,* myContacts,Mobile,01087304852
최석배형님(성일로스타),,,,,,,,,,,,,,,,* myContacts,Home,‎010-4233-5448
최준호 제이씨산업,,,,,,,,,,,,,,,,* myContacts,Mobile,01068590550
콘크리트 타설,,최철원,,,,,,,,,,,,,,* myContacts,Mobile,010-3278-7318
현수주임(LSS),,최,,,,,,,,,,,,,,Restored from Blackberry - BBF100-6 ::: * myContacts,,01062815532
최희철주임,,,,,,,,,,,,,,,,* myContacts,Mobile,01027450393
칭구칭구,,,,,,,,,,,,,,,,* myContacts,Mobile,01056014202
캠써치 안영주부장,,,,,,,,,,,,,,,,* myContacts,Mobile,01033913099
담당자),,코어(던킨,,,,,,,,,,,,,,* myContacts,,01031613404
코지공작소 물탱크 펌프,,,,,,,,,,,,,,,,* myContacts,Mobile,01074960801
크레인실 에어컨 기사,,,,,,,,,,,,,,,,* myContacts,Mobile,01039550864
탐진에이알사장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01052734973
,,택배차량 찍힘사고,,,,,,,,,,,,,,* myContacts,Mobile,010-8842-0461
터빈실 에어컨 공사,,,,,,,,,,,,,,,,* myContacts,Mobile,01073349699
,,폐소화기수거업체 (제주ENG),,,,,,,,,,,,,,* myContacts,Mobile,010-9515-8250
폐수처리업체,,,,,,,,,,,,,,,,* myContacts,Mobile,01023758017
폐유,,,,,,,,,,,,,,,,* myContacts,Mobile,01048798824
포티형님,,,,,,,,,,,,,,,,* myContacts,Mobile,01028911301
풍력발전기 케이렘 업체,,,,,,,,,,,,,,,,* myContacts,Mobile,01057678804
프레스이주원형님(성일로스타),,,,,,,,,,,,,,,,Blackberry - BBB100-1에서 복원됨 ::: * myContacts,,01024720890
하윤기  차장 셀텍,,,,,,,,,,,,,,,,* myContacts,Mobile,01071615350
하이엠솔루텍,,,,,,,,,,,,,,,,* myContacts,Mobile,01075666860
한국공조 곽병수 팀장님( 에어컨시공),,,,,,,,,,,,,,,,* myContacts,Mobile,01066011220
한라호이스트,,,,,,,,,,,,,,,,* myContacts,Mobile,01026952593
한화 카페 김린아주임님,,,,,,,,,,,,,,,,* myContacts,Mobile,01020490577
한화카페 고래상어 관리자,,,,,,,,,,,,,,,,* myContacts,Mobile,01049091128
,,해밀(물고기아크릴),,,,,,,,,,,,,,* myContacts,Mobile,010-8662-7977
현대리님(제주환경자원순환센터),,,,,,,,,,,,,,,,* myContacts,Mobile,01045564612
,,현동빈주임(기프트샵),,,,,,,,,,,,,,* myContacts,Mobile,010-8326-2022
현진우기사,,,,,,,,,,,,,,,,* myContacts,Mobile,01091348638
,,혜진,,,,,,,,,,,,,,* myContacts,Mobile,010-3725-5892
홍선익 부산벨트,,,,,,,,,,,,,,,,* myContacts,Mobile,01026915621
홍성원 계장님(어류파트),,,,,,,,,,,,,,,,* myContacts,Mobile,01035834581
홍원희과장님(메디컬센터),,,,,,,,,,,,,,,,* myContacts,Mobile,01096667801
,,홍준기,,,,,,,,,,,,,,* myContacts,Mobile,010-9617-3977
홍현석 주임 기계(자원환경순환센터),,,,,,,,,,,,,,,,* myContacts,Mobile,01099600786
,,황시애(민초),,,,,,,,,,,,,,* myContacts,Mobile,010-9324-1284
이월형,,황지훈,,,,,,,,,,,,,,* myContacts,Mobile,010-2277-7071
태민주임님(LSS),,황,,,,,,,,,,,,,,Restored from Blackberry - BBF100-6 ::: * myContacts,,01057787958
,,효성기전 팀장님,,,,,,,,,,,,,,* myContacts,Mobile,010-9055-4893
재형님,,휘,,,,,,,,,,,,,,* myContacts,Mobile,010-9431-6259
흡수식냉동기 서재욱지사장님,,,,,,,,,,,,,,,,* myContacts,Mobile,01028255273
,,히릭,,,,,,,,,,,,,,* myContacts,Mobile,010-9060-0677
"""
    parsed_contacts = parse_contacts(sample_file_content)
    for contact in parsed_contacts:
        print(contact)

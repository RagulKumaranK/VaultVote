/**
 * VaultVote Location Dataset
 * Fast offline autocomplete for District -> State & PIN Code
 */

const INDIA_LOCATIONS = [
  {
    "district": "Ariyalur",
    "state": "Tamil Nadu",
    "pincode": "621704",
    "aliases": [
      "ariyalur"
    ]
  },
  {
    "district": "Chengalpattu",
    "state": "Tamil Nadu",
    "pincode": "603001",
    "aliases": [
      "chengalpattu",
      "chengalpet"
    ]
  },
  {
    "district": "Chennai",
    "state": "Tamil Nadu",
    "pincode": "600001",
    "aliases": [
      "chennai",
      "madras"
    ]
  },
  {
    "district": "Coimbatore",
    "state": "Tamil Nadu",
    "pincode": "641001",
    "aliases": [
      "coimbatore",
      "kovai"
    ]
  },
  {
    "district": "Cuddalore",
    "state": "Tamil Nadu",
    "pincode": "607001",
    "aliases": [
      "cuddalore"
    ]
  },
  {
    "district": "Dharmapuri",
    "state": "Tamil Nadu",
    "pincode": "636701",
    "aliases": [
      "dharmapuri"
    ]
  },
  {
    "district": "Dindigul",
    "state": "Tamil Nadu",
    "pincode": "624001",
    "aliases": [
      "dindigul"
    ]
  },
  {
    "district": "Erode",
    "state": "Tamil Nadu",
    "pincode": "638001",
    "aliases": [
      "erode"
    ]
  },
  {
    "district": "Kallakurichi",
    "state": "Tamil Nadu",
    "pincode": "606202",
    "aliases": [
      "kallakurichi"
    ]
  },
  {
    "district": "Kanchipuram",
    "state": "Tamil Nadu",
    "pincode": "631501",
    "aliases": [
      "kanchipuram",
      "kanchi"
    ]
  },
  {
    "district": "Kanyakumari",
    "state": "Tamil Nadu",
    "pincode": "629001",
    "aliases": [
      "kanyakumari",
      "nagercoil"
    ]
  },
  {
    "district": "Karur",
    "state": "Tamil Nadu",
    "pincode": "639001",
    "aliases": [
      "karur"
    ]
  },
  {
    "district": "Krishnagiri",
    "state": "Tamil Nadu",
    "pincode": "635001",
    "aliases": [
      "krishnagiri"
    ]
  },
  {
    "district": "Madurai",
    "state": "Tamil Nadu",
    "pincode": "625001",
    "aliases": [
      "madurai"
    ]
  },
  {
    "district": "Mayiladuthurai",
    "state": "Tamil Nadu",
    "pincode": "609001",
    "aliases": [
      "mayiladuthurai",
      "mayavaram"
    ]
  },
  {
    "district": "Nagapattinam",
    "state": "Tamil Nadu",
    "pincode": "611001",
    "aliases": [
      "nagapattinam"
    ]
  },
  {
    "district": "Namakkal",
    "state": "Tamil Nadu",
    "pincode": "637001",
    "aliases": [
      "namakkal"
    ]
  },
  {
    "district": "Nilgiris",
    "state": "Tamil Nadu",
    "pincode": "643001",
    "aliases": [
      "nilgiris",
      "ooty",
      "udhagamandalam"
    ]
  },
  {
    "district": "Perambalur",
    "state": "Tamil Nadu",
    "pincode": "621212",
    "aliases": [
      "perambalur"
    ]
  },
  {
    "district": "Pudukkottai",
    "state": "Tamil Nadu",
    "pincode": "622001",
    "aliases": [
      "pudukkottai"
    ]
  },
  {
    "district": "Ramanathapuram",
    "state": "Tamil Nadu",
    "pincode": "623501",
    "aliases": [
      "ramanathapuram",
      "ramnad"
    ]
  },
  {
    "district": "Ranipet",
    "state": "Tamil Nadu",
    "pincode": "632401",
    "aliases": [
      "ranipet"
    ]
  },
  {
    "district": "Salem",
    "state": "Tamil Nadu",
    "pincode": "636001",
    "aliases": [
      "salem"
    ]
  },
  {
    "district": "Sivaganga",
    "state": "Tamil Nadu",
    "pincode": "630561",
    "aliases": [
      "sivaganga",
      "sivagangai"
    ]
  },
  {
    "district": "Tenkasi",
    "state": "Tamil Nadu",
    "pincode": "627811",
    "aliases": [
      "tenkasi"
    ]
  },
  {
    "district": "Thanjavur",
    "state": "Tamil Nadu",
    "pincode": "613001",
    "aliases": [
      "thanjavur",
      "tanjore"
    ]
  },
  {
    "district": "Theni",
    "state": "Tamil Nadu",
    "pincode": "625531",
    "aliases": [
      "theni"
    ]
  },
  {
    "district": "Thoothukudi",
    "state": "Tamil Nadu",
    "pincode": "628001",
    "aliases": [
      "thoothukudi",
      "tuticorin"
    ]
  },
  {
    "district": "Tiruchirappalli",
    "state": "Tamil Nadu",
    "pincode": "620001",
    "aliases": [
      "tiruchirappalli",
      "trichy",
      "tiruchi"
    ]
  },
  {
    "district": "Tirunelveli",
    "state": "Tamil Nadu",
    "pincode": "627001",
    "aliases": [
      "tirunelveli",
      "nellai"
    ]
  },
  {
    "district": "Tirupathur",
    "state": "Tamil Nadu",
    "pincode": "635601",
    "aliases": [
      "tirupathur"
    ]
  },
  {
    "district": "Tiruppur",
    "state": "Tamil Nadu",
    "pincode": "641601",
    "aliases": [
      "tiruppur",
      "tirupur"
    ]
  },
  {
    "district": "Tiruvallur",
    "state": "Tamil Nadu",
    "pincode": "602001",
    "aliases": [
      "tiruvallur",
      "thiruvallur"
    ]
  },
  {
    "district": "Tiruvannamalai",
    "state": "Tamil Nadu",
    "pincode": "606601",
    "aliases": [
      "tiruvannamalai"
    ]
  },
  {
    "district": "Tiruvarur",
    "state": "Tamil Nadu",
    "pincode": "610001",
    "aliases": [
      "tiruvarur",
      "thiruvarur"
    ]
  },
  {
    "district": "Vellore",
    "state": "Tamil Nadu",
    "pincode": "632001",
    "aliases": [
      "vellore"
    ]
  },
  {
    "district": "Viluppuram",
    "state": "Tamil Nadu",
    "pincode": "605602",
    "aliases": [
      "viluppuram",
      "villupuram"
    ]
  },
  {
    "district": "Virudhunagar",
    "state": "Tamil Nadu",
    "pincode": "626001",
    "aliases": [
      "virudhunagar"
    ]
  },
  {
    "district": "Bagalkot",
    "state": "Karnataka",
    "pincode": "587101",
    "aliases": [
      "bagalkot",
      "bagalkote"
    ]
  },
  {
    "district": "Ballari",
    "state": "Karnataka",
    "pincode": "583101",
    "aliases": [
      "ballari",
      "bellary"
    ]
  },
  {
    "district": "Belagavi",
    "state": "Karnataka",
    "pincode": "590001",
    "aliases": [
      "belagavi",
      "belgaum"
    ]
  },
  {
    "district": "Bengaluru Rural",
    "state": "Karnataka",
    "pincode": "562123",
    "aliases": [
      "bengaluru rural",
      "bangalore rural"
    ]
  },
  {
    "district": "Bengaluru Urban",
    "state": "Karnataka",
    "pincode": "560001",
    "aliases": [
      "bengaluru urban",
      "bengaluru",
      "bangalore",
      "bangalore urban"
    ]
  },
  {
    "district": "Bidar",
    "state": "Karnataka",
    "pincode": "585401",
    "aliases": [
      "bidar"
    ]
  },
  {
    "district": "Chamarajanagar",
    "state": "Karnataka",
    "pincode": "571313",
    "aliases": [
      "chamarajanagar"
    ]
  },
  {
    "district": "Chikkaballapur",
    "state": "Karnataka",
    "pincode": "562101",
    "aliases": [
      "chikkaballapur"
    ]
  },
  {
    "district": "Chikkamagaluru",
    "state": "Karnataka",
    "pincode": "577101",
    "aliases": [
      "chikkamagaluru",
      "chikmagalur"
    ]
  },
  {
    "district": "Chitradurga",
    "state": "Karnataka",
    "pincode": "577501",
    "aliases": [
      "chitradurga"
    ]
  },
  {
    "district": "Dakshina Kannada",
    "state": "Karnataka",
    "pincode": "575001",
    "aliases": [
      "dakshina kannada",
      "mangalore",
      "mangaluru"
    ]
  },
  {
    "district": "Davanagere",
    "state": "Karnataka",
    "pincode": "577001",
    "aliases": [
      "davanagere"
    ]
  },
  {
    "district": "Dharwad",
    "state": "Karnataka",
    "pincode": "580001",
    "aliases": [
      "dharwad",
      "hubli",
      "hubballi"
    ]
  },
  {
    "district": "Gadag",
    "state": "Karnataka",
    "pincode": "582101",
    "aliases": [
      "gadag"
    ]
  },
  {
    "district": "Hassan",
    "state": "Karnataka",
    "pincode": "573201",
    "aliases": [
      "hassan"
    ]
  },
  {
    "district": "Haveri",
    "state": "Karnataka",
    "pincode": "581110",
    "aliases": [
      "haveri"
    ]
  },
  {
    "district": "Kalaburagi",
    "state": "Karnataka",
    "pincode": "585101",
    "aliases": [
      "kalaburagi",
      "gulbarga"
    ]
  },
  {
    "district": "Kodagu",
    "state": "Karnataka",
    "pincode": "571201",
    "aliases": [
      "kodagu",
      "coorg",
      "madikeri"
    ]
  },
  {
    "district": "Kolar",
    "state": "Karnataka",
    "pincode": "563101",
    "aliases": [
      "kolar"
    ]
  },
  {
    "district": "Koppal",
    "state": "Karnataka",
    "pincode": "583231",
    "aliases": [
      "koppal"
    ]
  },
  {
    "district": "Mandya",
    "state": "Karnataka",
    "pincode": "571401",
    "aliases": [
      "mandya"
    ]
  },
  {
    "district": "Mysuru",
    "state": "Karnataka",
    "pincode": "570001",
    "aliases": [
      "mysuru",
      "mysore"
    ]
  },
  {
    "district": "Raichur",
    "state": "Karnataka",
    "pincode": "584101",
    "aliases": [
      "raichur"
    ]
  },
  {
    "district": "Ramanagara",
    "state": "Karnataka",
    "pincode": "562159",
    "aliases": [
      "ramanagara",
      "ramanagar"
    ]
  },
  {
    "district": "Shivamogga",
    "state": "Karnataka",
    "pincode": "577201",
    "aliases": [
      "shivamogga",
      "shimoga"
    ]
  },
  {
    "district": "Tumakuru",
    "state": "Karnataka",
    "pincode": "572101",
    "aliases": [
      "tumakuru",
      "tumkur"
    ]
  },
  {
    "district": "Udupi",
    "state": "Karnataka",
    "pincode": "576101",
    "aliases": [
      "udupi"
    ]
  },
  {
    "district": "Uttara Kannada",
    "state": "Karnataka",
    "pincode": "581301",
    "aliases": [
      "uttara kannada",
      "karwar"
    ]
  },
  {
    "district": "Vijayanagara",
    "state": "Karnataka",
    "pincode": "583201",
    "aliases": [
      "vijayanagara",
      "hospet"
    ]
  },
  {
    "district": "Vijayapura",
    "state": "Karnataka",
    "pincode": "586101",
    "aliases": [
      "vijayapura",
      "bijapur"
    ]
  },
  {
    "district": "Yadgir",
    "state": "Karnataka",
    "pincode": "585202",
    "aliases": [
      "yadgir"
    ]
  },
  {
    "district": "Alappuzha",
    "state": "Kerala",
    "pincode": "688001",
    "aliases": [
      "alappuzha",
      "alleppey"
    ]
  },
  {
    "district": "Ernakulam",
    "state": "Kerala",
    "pincode": "682011",
    "aliases": [
      "ernakulam",
      "kochi",
      "cochin"
    ]
  },
  {
    "district": "Idukki",
    "state": "Kerala",
    "pincode": "685603",
    "aliases": [
      "idukki",
      "painavu"
    ]
  },
  {
    "district": "Kannur",
    "state": "Kerala",
    "pincode": "670001",
    "aliases": [
      "kannur",
      "cannanore"
    ]
  },
  {
    "district": "Kasaragod",
    "state": "Kerala",
    "pincode": "671121",
    "aliases": [
      "kasaragod"
    ]
  },
  {
    "district": "Kollam",
    "state": "Kerala",
    "pincode": "691001",
    "aliases": [
      "kollam",
      "quilon"
    ]
  },
  {
    "district": "Kottayam",
    "state": "Kerala",
    "pincode": "686001",
    "aliases": [
      "kottayam"
    ]
  },
  {
    "district": "Kozhikode",
    "state": "Kerala",
    "pincode": "673001",
    "aliases": [
      "kozhikode",
      "calicut"
    ]
  },
  {
    "district": "Malappuram",
    "state": "Kerala",
    "pincode": "676505",
    "aliases": [
      "malappuram"
    ]
  },
  {
    "district": "Palakkad",
    "state": "Kerala",
    "pincode": "678001",
    "aliases": [
      "palakkad",
      "palghat"
    ]
  },
  {
    "district": "Pathanamthitta",
    "state": "Kerala",
    "pincode": "689645",
    "aliases": [
      "pathanamthitta"
    ]
  },
  {
    "district": "Thiruvananthapuram",
    "state": "Kerala",
    "pincode": "695001",
    "aliases": [
      "thiruvananthapuram",
      "trivandrum"
    ]
  },
  {
    "district": "Thrissur",
    "state": "Kerala",
    "pincode": "680001",
    "aliases": [
      "thrissur",
      "trichur"
    ]
  },
  {
    "district": "Wayanad",
    "state": "Kerala",
    "pincode": "673121",
    "aliases": [
      "wayanad",
      "kalpetta"
    ]
  },
  {
    "district": "Alluri Sitharama Raju",
    "state": "Andhra Pradesh",
    "pincode": "531117",
    "aliases": [
      "alluri"
    ]
  },
  {
    "district": "Anakapalli",
    "state": "Andhra Pradesh",
    "pincode": "531001",
    "aliases": [
      "anakapalli"
    ]
  },
  {
    "district": "Ananthapuramu",
    "state": "Andhra Pradesh",
    "pincode": "515001",
    "aliases": [
      "anantapur",
      "ananthapuramu"
    ]
  },
  {
    "district": "Annamayya",
    "state": "Andhra Pradesh",
    "pincode": "516101",
    "aliases": [
      "annamayya",
      "rayachoty"
    ]
  },
  {
    "district": "Bapatla",
    "state": "Andhra Pradesh",
    "pincode": "522101",
    "aliases": [
      "bapatla"
    ]
  },
  {
    "district": "Chittoor",
    "state": "Andhra Pradesh",
    "pincode": "517001",
    "aliases": [
      "chittoor"
    ]
  },
  {
    "district": "Dr. B.R. Ambedkar Konaseema",
    "state": "Andhra Pradesh",
    "pincode": "533201",
    "aliases": [
      "konaseema",
      "amalapuram"
    ]
  },
  {
    "district": "East Godavari",
    "state": "Andhra Pradesh",
    "pincode": "533101",
    "aliases": [
      "east godavari",
      "rajahmundry"
    ]
  },
  {
    "district": "Eluru",
    "state": "Andhra Pradesh",
    "pincode": "534001",
    "aliases": [
      "eluru"
    ]
  },
  {
    "district": "Guntur",
    "state": "Andhra Pradesh",
    "pincode": "522001",
    "aliases": [
      "guntur"
    ]
  },
  {
    "district": "Kakinada",
    "state": "Andhra Pradesh",
    "pincode": "533001",
    "aliases": [
      "kakinada"
    ]
  },
  {
    "district": "Krishna",
    "state": "Andhra Pradesh",
    "pincode": "521001",
    "aliases": [
      "krishna",
      "machilipatnam"
    ]
  },
  {
    "district": "Kurnool",
    "state": "Andhra Pradesh",
    "pincode": "518001",
    "aliases": [
      "kurnool"
    ]
  },
  {
    "district": "Nandyal",
    "state": "Andhra Pradesh",
    "pincode": "518501",
    "aliases": [
      "nandyal"
    ]
  },
  {
    "district": "NTR",
    "state": "Andhra Pradesh",
    "pincode": "520001",
    "aliases": [
      "ntr",
      "vijayawada"
    ]
  },
  {
    "district": "Palnadu",
    "state": "Andhra Pradesh",
    "pincode": "522601",
    "aliases": [
      "palnadu",
      "narasaraopet"
    ]
  },
  {
    "district": "Parvathipuram Manyam",
    "state": "Andhra Pradesh",
    "pincode": "535501",
    "aliases": [
      "parvathipuram"
    ]
  },
  {
    "district": "Prakasam",
    "state": "Andhra Pradesh",
    "pincode": "523001",
    "aliases": [
      "prakasam",
      "ongole"
    ]
  },
  {
    "district": "Sri Potti Sriramulu Nellore",
    "state": "Andhra Pradesh",
    "pincode": "524001",
    "aliases": [
      "nellore",
      "sps nellore"
    ]
  },
  {
    "district": "Sri Sathya Sai",
    "state": "Andhra Pradesh",
    "pincode": "515134",
    "aliases": [
      "sri sathya sai",
      "puttaparthi"
    ]
  },
  {
    "district": "Srikakulam",
    "state": "Andhra Pradesh",
    "pincode": "532001",
    "aliases": [
      "srikakulam"
    ]
  },
  {
    "district": "Tirupati",
    "state": "Andhra Pradesh",
    "pincode": "517501",
    "aliases": [
      "tirupati"
    ]
  },
  {
    "district": "Visakhapatnam",
    "state": "Andhra Pradesh",
    "pincode": "530001",
    "aliases": [
      "visakhapatnam",
      "vizag"
    ]
  },
  {
    "district": "Vizianagaram",
    "state": "Andhra Pradesh",
    "pincode": "535001",
    "aliases": [
      "vizianagaram"
    ]
  },
  {
    "district": "West Godavari",
    "state": "Andhra Pradesh",
    "pincode": "534201",
    "aliases": [
      "west godavari",
      "bhimavaram"
    ]
  },
  {
    "district": "YSR Kadapa",
    "state": "Andhra Pradesh",
    "pincode": "516001",
    "aliases": [
      "kadapa",
      "ysr"
    ]
  },
  {
    "district": "Adilabad",
    "state": "Telangana",
    "pincode": "504001",
    "aliases": [
      "adilabad"
    ]
  },
  {
    "district": "Bhadradri Kothagudem",
    "state": "Telangana",
    "pincode": "507101",
    "aliases": [
      "kothagudem"
    ]
  },
  {
    "district": "Hanumakonda",
    "state": "Telangana",
    "pincode": "506001",
    "aliases": [
      "hanumakonda",
      "warangal urban"
    ]
  },
  {
    "district": "Hyderabad",
    "state": "Telangana",
    "pincode": "500001",
    "aliases": [
      "hyderabad",
      "secunderabad"
    ]
  },
  {
    "district": "Jagtial",
    "state": "Telangana",
    "pincode": "505327",
    "aliases": [
      "jagtial"
    ]
  },
  {
    "district": "Jangaon",
    "state": "Telangana",
    "pincode": "506167",
    "aliases": [
      "jangaon"
    ]
  },
  {
    "district": "Jayashankar Bhupalpally",
    "state": "Telangana",
    "pincode": "506169",
    "aliases": [
      "bhupalpally"
    ]
  },
  {
    "district": "Jogulamba Gadwal",
    "state": "Telangana",
    "pincode": "509125",
    "aliases": [
      "gadwal"
    ]
  },
  {
    "district": "Kamareddy",
    "state": "Telangana",
    "pincode": "503111",
    "aliases": [
      "kamareddy"
    ]
  },
  {
    "district": "Karimnagar",
    "state": "Telangana",
    "pincode": "505001",
    "aliases": [
      "karimnagar"
    ]
  },
  {
    "district": "Khammam",
    "state": "Telangana",
    "pincode": "507001",
    "aliases": [
      "khammam"
    ]
  },
  {
    "district": "Kumuram Bheem Asifabad",
    "state": "Telangana",
    "pincode": "504293",
    "aliases": [
      "asifabad"
    ]
  },
  {
    "district": "Mahabubabad",
    "state": "Telangana",
    "pincode": "506101",
    "aliases": [
      "mahabubabad"
    ]
  },
  {
    "district": "Mahabubnagar",
    "state": "Telangana",
    "pincode": "509001",
    "aliases": [
      "mahabubnagar"
    ]
  },
  {
    "district": "Mancherial",
    "state": "Telangana",
    "pincode": "504208",
    "aliases": [
      "mancherial"
    ]
  },
  {
    "district": "Medak",
    "state": "Telangana",
    "pincode": "502110",
    "aliases": [
      "medak"
    ]
  },
  {
    "district": "Medchal-Malkajgiri",
    "state": "Telangana",
    "pincode": "500047",
    "aliases": [
      "medchal",
      "malkajgiri"
    ]
  },
  {
    "district": "Mulugu",
    "state": "Telangana",
    "pincode": "506343",
    "aliases": [
      "mulugu"
    ]
  },
  {
    "district": "Nagarkurnool",
    "state": "Telangana",
    "pincode": "509209",
    "aliases": [
      "nagarkurnool"
    ]
  },
  {
    "district": "Nalgonda",
    "state": "Telangana",
    "pincode": "508001",
    "aliases": [
      "nalgonda"
    ]
  },
  {
    "district": "Narayanpet",
    "state": "Telangana",
    "pincode": "509210",
    "aliases": [
      "narayanpet"
    ]
  },
  {
    "district": "Nirmal",
    "state": "Telangana",
    "pincode": "504106",
    "aliases": [
      "nirmal"
    ]
  },
  {
    "district": "Nizamabad",
    "state": "Telangana",
    "pincode": "503001",
    "aliases": [
      "nizamabad"
    ]
  },
  {
    "district": "Peddapalli",
    "state": "Telangana",
    "pincode": "505172",
    "aliases": [
      "peddapalli"
    ]
  },
  {
    "district": "Rajanna Sircilla",
    "state": "Telangana",
    "pincode": "505301",
    "aliases": [
      "sircilla"
    ]
  },
  {
    "district": "Ranga Reddy",
    "state": "Telangana",
    "pincode": "500030",
    "aliases": [
      "rangareddy",
      "ranga reddy"
    ]
  },
  {
    "district": "Sangareddy",
    "state": "Telangana",
    "pincode": "502001",
    "aliases": [
      "sangareddy"
    ]
  },
  {
    "district": "Siddipet",
    "state": "Telangana",
    "pincode": "502103",
    "aliases": [
      "siddipet"
    ]
  },
  {
    "district": "Suryapet",
    "state": "Telangana",
    "pincode": "508213",
    "aliases": [
      "suryapet"
    ]
  },
  {
    "district": "Vikarabad",
    "state": "Telangana",
    "pincode": "501101",
    "aliases": [
      "vikarabad"
    ]
  },
  {
    "district": "Wanaparthy",
    "state": "Telangana",
    "pincode": "509103",
    "aliases": [
      "wanaparthy"
    ]
  },
  {
    "district": "Warangal",
    "state": "Telangana",
    "pincode": "506002",
    "aliases": [
      "warangal"
    ]
  },
  {
    "district": "Yadadri Bhuvanagiri",
    "state": "Telangana",
    "pincode": "508116",
    "aliases": [
      "bhuvanagiri",
      "bhongir"
    ]
  },
  {
    "district": "Ahmednagar",
    "state": "Maharashtra",
    "pincode": "414001",
    "aliases": [
      "ahmednagar",
      "ahilyanagar"
    ]
  },
  {
    "district": "Akola",
    "state": "Maharashtra",
    "pincode": "444001",
    "aliases": [
      "akola"
    ]
  },
  {
    "district": "Amravati",
    "state": "Maharashtra",
    "pincode": "444601",
    "aliases": [
      "amravati"
    ]
  },
  {
    "district": "Chhatrapati Sambhajinagar",
    "state": "Maharashtra",
    "pincode": "431001",
    "aliases": [
      "chhatrapati sambhajinagar",
      "aurangabad"
    ]
  },
  {
    "district": "Beed",
    "state": "Maharashtra",
    "pincode": "431122",
    "aliases": [
      "beed"
    ]
  },
  {
    "district": "Bhandara",
    "state": "Maharashtra",
    "pincode": "441904",
    "aliases": [
      "bhandara"
    ]
  },
  {
    "district": "Buldhana",
    "state": "Maharashtra",
    "pincode": "443001",
    "aliases": [
      "buldhana"
    ]
  },
  {
    "district": "Chandrapur",
    "state": "Maharashtra",
    "pincode": "442401",
    "aliases": [
      "chandrapur"
    ]
  },
  {
    "district": "Dhule",
    "state": "Maharashtra",
    "pincode": "424001",
    "aliases": [
      "dhule"
    ]
  },
  {
    "district": "Gadchiroli",
    "state": "Maharashtra",
    "pincode": "442605",
    "aliases": [
      "gadchiroli"
    ]
  },
  {
    "district": "Gondia",
    "state": "Maharashtra",
    "pincode": "441601",
    "aliases": [
      "gondia"
    ]
  },
  {
    "district": "Hingoli",
    "state": "Maharashtra",
    "pincode": "431513",
    "aliases": [
      "hingoli"
    ]
  },
  {
    "district": "Jalgaon",
    "state": "Maharashtra",
    "pincode": "425001",
    "aliases": [
      "jalgaon"
    ]
  },
  {
    "district": "Jalna",
    "state": "Maharashtra",
    "pincode": "431203",
    "aliases": [
      "jalna"
    ]
  },
  {
    "district": "Kolhapur",
    "state": "Maharashtra",
    "pincode": "416001",
    "aliases": [
      "kolhapur"
    ]
  },
  {
    "district": "Latur",
    "state": "Maharashtra",
    "pincode": "413512",
    "aliases": [
      "latur"
    ]
  },
  {
    "district": "Mumbai City",
    "state": "Maharashtra",
    "pincode": "400001",
    "aliases": [
      "mumbai",
      "mumbai city",
      "bombay"
    ]
  },
  {
    "district": "Mumbai Suburban",
    "state": "Maharashtra",
    "pincode": "400051",
    "aliases": [
      "mumbai suburban",
      "bandra",
      "andheri"
    ]
  },
  {
    "district": "Nagpur",
    "state": "Maharashtra",
    "pincode": "440001",
    "aliases": [
      "nagpur"
    ]
  },
  {
    "district": "Nanded",
    "state": "Maharashtra",
    "pincode": "431601",
    "aliases": [
      "nanded"
    ]
  },
  {
    "district": "Nandurbar",
    "state": "Maharashtra",
    "pincode": "425412",
    "aliases": [
      "nandurbar"
    ]
  },
  {
    "district": "Nashik",
    "state": "Maharashtra",
    "pincode": "422001",
    "aliases": [
      "nashik",
      "nasik"
    ]
  },
  {
    "district": "Dharashiv",
    "state": "Maharashtra",
    "pincode": "413501",
    "aliases": [
      "dharashiv",
      "osmanabad"
    ]
  },
  {
    "district": "Palghar",
    "state": "Maharashtra",
    "pincode": "401404",
    "aliases": [
      "palghar"
    ]
  },
  {
    "district": "Parbhani",
    "state": "Maharashtra",
    "pincode": "431401",
    "aliases": [
      "parbhani"
    ]
  },
  {
    "district": "Pune",
    "state": "Maharashtra",
    "pincode": "411001",
    "aliases": [
      "pune",
      "poona"
    ]
  },
  {
    "district": "Raigad",
    "state": "Maharashtra",
    "pincode": "402201",
    "aliases": [
      "raigad",
      "alibag"
    ]
  },
  {
    "district": "Ratnagiri",
    "state": "Maharashtra",
    "pincode": "415612",
    "aliases": [
      "ratnagiri"
    ]
  },
  {
    "district": "Sangli",
    "state": "Maharashtra",
    "pincode": "416416",
    "aliases": [
      "sangli"
    ]
  },
  {
    "district": "Satara",
    "state": "Maharashtra",
    "pincode": "415001",
    "aliases": [
      "satara"
    ]
  },
  {
    "district": "Sindhudurg",
    "state": "Maharashtra",
    "pincode": "416812",
    "aliases": [
      "sindhudurg"
    ]
  },
  {
    "district": "Solapur",
    "state": "Maharashtra",
    "pincode": "413001",
    "aliases": [
      "solapur",
      "sholapur"
    ]
  },
  {
    "district": "Thane",
    "state": "Maharashtra",
    "pincode": "400601",
    "aliases": [
      "thane"
    ]
  },
  {
    "district": "Wardha",
    "state": "Maharashtra",
    "pincode": "442001",
    "aliases": [
      "wardha"
    ]
  },
  {
    "district": "Washim",
    "state": "Maharashtra",
    "pincode": "444505",
    "aliases": [
      "washim"
    ]
  },
  {
    "district": "Yavatmal",
    "state": "Maharashtra",
    "pincode": "445001",
    "aliases": [
      "yavatmal"
    ]
  },
  {
    "district": "Central Delhi",
    "state": "Delhi",
    "pincode": "110001",
    "aliases": [
      "central delhi",
      "connaught place"
    ]
  },
  {
    "district": "East Delhi",
    "state": "Delhi",
    "pincode": "110092",
    "aliases": [
      "east delhi"
    ]
  },
  {
    "district": "New Delhi",
    "state": "Delhi",
    "pincode": "110001",
    "aliases": [
      "new delhi",
      "delhi"
    ]
  },
  {
    "district": "North Delhi",
    "state": "Delhi",
    "pincode": "110007",
    "aliases": [
      "north delhi"
    ]
  },
  {
    "district": "North East Delhi",
    "state": "Delhi",
    "pincode": "110053",
    "aliases": [
      "north east delhi"
    ]
  },
  {
    "district": "North West Delhi",
    "state": "Delhi",
    "pincode": "110085",
    "aliases": [
      "north west delhi"
    ]
  },
  {
    "district": "Shahdara",
    "state": "Delhi",
    "pincode": "110032",
    "aliases": [
      "shahdara"
    ]
  },
  {
    "district": "South Delhi",
    "state": "Delhi",
    "pincode": "110017",
    "aliases": [
      "south delhi"
    ]
  },
  {
    "district": "South East Delhi",
    "state": "Delhi",
    "pincode": "110019",
    "aliases": [
      "south east delhi"
    ]
  },
  {
    "district": "South West Delhi",
    "state": "Delhi",
    "pincode": "110075",
    "aliases": [
      "south west delhi",
      "dwarka"
    ]
  },
  {
    "district": "West Delhi",
    "state": "Delhi",
    "pincode": "110027",
    "aliases": [
      "west delhi"
    ]
  },
  {
    "district": "Ahmedabad",
    "state": "Gujarat",
    "pincode": "380001",
    "aliases": [
      "ahmedabad"
    ]
  },
  {
    "district": "Amreli",
    "state": "Gujarat",
    "pincode": "365601",
    "aliases": [
      "amreli"
    ]
  },
  {
    "district": "Anand",
    "state": "Gujarat",
    "pincode": "388001",
    "aliases": [
      "anand"
    ]
  },
  {
    "district": "Aravalli",
    "state": "Gujarat",
    "pincode": "383315",
    "aliases": [
      "aravalli"
    ]
  },
  {
    "district": "Banaskantha",
    "state": "Gujarat",
    "pincode": "385001",
    "aliases": [
      "banaskantha",
      "palanpur"
    ]
  },
  {
    "district": "Bharuch",
    "state": "Gujarat",
    "pincode": "392001",
    "aliases": [
      "bharuch"
    ]
  },
  {
    "district": "Bhavnagar",
    "state": "Gujarat",
    "pincode": "364001",
    "aliases": [
      "bhavnagar"
    ]
  },
  {
    "district": "Botad",
    "state": "Gujarat",
    "pincode": "364710",
    "aliases": [
      "botad"
    ]
  },
  {
    "district": "Chhota Udaipur",
    "state": "Gujarat",
    "pincode": "391165",
    "aliases": [
      "chhota udaipur"
    ]
  },
  {
    "district": "Dahod",
    "state": "Gujarat",
    "pincode": "389151",
    "aliases": [
      "dahod"
    ]
  },
  {
    "district": "Dang",
    "state": "Gujarat",
    "pincode": "394710",
    "aliases": [
      "dang",
      "ahwa"
    ]
  },
  {
    "district": "Devbhumi Dwarka",
    "state": "Gujarat",
    "pincode": "361305",
    "aliases": [
      "dwarka",
      "devbhumi dwarka"
    ]
  },
  {
    "district": "Gandhinagar",
    "state": "Gujarat",
    "pincode": "382010",
    "aliases": [
      "gandhinagar"
    ]
  },
  {
    "district": "Gir Somnath",
    "state": "Gujarat",
    "pincode": "362265",
    "aliases": [
      "gir somnath",
      "veraval"
    ]
  },
  {
    "district": "Jamnagar",
    "state": "Gujarat",
    "pincode": "361001",
    "aliases": [
      "jamnagar"
    ]
  },
  {
    "district": "Junagadh",
    "state": "Gujarat",
    "pincode": "362001",
    "aliases": [
      "junagadh"
    ]
  },
  {
    "district": "Kheda",
    "state": "Gujarat",
    "pincode": "387001",
    "aliases": [
      "kheda",
      "nadiad"
    ]
  },
  {
    "district": "Kutch",
    "state": "Gujarat",
    "pincode": "370001",
    "aliases": [
      "kutch",
      "bhuj",
      "kachchh"
    ]
  },
  {
    "district": "Mahisagar",
    "state": "Gujarat",
    "pincode": "389230",
    "aliases": [
      "mahisagar",
      "lunawada"
    ]
  },
  {
    "district": "Mehsana",
    "state": "Gujarat",
    "pincode": "384001",
    "aliases": [
      "mehsana"
    ]
  },
  {
    "district": "Morbi",
    "state": "Gujarat",
    "pincode": "363641",
    "aliases": [
      "morbi"
    ]
  },
  {
    "district": "Narmada",
    "state": "Gujarat",
    "pincode": "393145",
    "aliases": [
      "narmada",
      "rajpipla"
    ]
  },
  {
    "district": "Navsari",
    "state": "Gujarat",
    "pincode": "396445",
    "aliases": [
      "navsari"
    ]
  },
  {
    "district": "Panchmahal",
    "state": "Gujarat",
    "pincode": "389001",
    "aliases": [
      "panchmahal",
      "godhra"
    ]
  },
  {
    "district": "Patan",
    "state": "Gujarat",
    "pincode": "384265",
    "aliases": [
      "patan"
    ]
  },
  {
    "district": "Porbandar",
    "state": "Gujarat",
    "pincode": "360575",
    "aliases": [
      "porbandar"
    ]
  },
  {
    "district": "Rajkot",
    "state": "Gujarat",
    "pincode": "360001",
    "aliases": [
      "rajkot"
    ]
  },
  {
    "district": "Sabarkantha",
    "state": "Gujarat",
    "pincode": "383001",
    "aliases": [
      "sabarkantha",
      "himatnagar"
    ]
  },
  {
    "district": "Surat",
    "state": "Gujarat",
    "pincode": "395001",
    "aliases": [
      "surat"
    ]
  },
  {
    "district": "Surendranagar",
    "state": "Gujarat",
    "pincode": "363001",
    "aliases": [
      "surendranagar"
    ]
  },
  {
    "district": "Tapi",
    "state": "Gujarat",
    "pincode": "394650",
    "aliases": [
      "tapi",
      "vyara"
    ]
  },
  {
    "district": "Vadodara",
    "state": "Gujarat",
    "pincode": "390001",
    "aliases": [
      "vadodara",
      "baroda"
    ]
  },
  {
    "district": "Valsad",
    "state": "Gujarat",
    "pincode": "396001",
    "aliases": [
      "valsad"
    ]
  },
  {
    "district": "Ajmer",
    "state": "Rajasthan",
    "pincode": "305001",
    "aliases": [
      "ajmer"
    ]
  },
  {
    "district": "Alwar",
    "state": "Rajasthan",
    "pincode": "301001",
    "aliases": [
      "alwar"
    ]
  },
  {
    "district": "Banswara",
    "state": "Rajasthan",
    "pincode": "327001",
    "aliases": [
      "banswara"
    ]
  },
  {
    "district": "Baran",
    "state": "Rajasthan",
    "pincode": "325205",
    "aliases": [
      "baran"
    ]
  },
  {
    "district": "Barmer",
    "state": "Rajasthan",
    "pincode": "344001",
    "aliases": [
      "barmer"
    ]
  },
  {
    "district": "Bharatpur",
    "state": "Rajasthan",
    "pincode": "321001",
    "aliases": [
      "bharatpur"
    ]
  },
  {
    "district": "Bhilwara",
    "state": "Rajasthan",
    "pincode": "311001",
    "aliases": [
      "bhilwara"
    ]
  },
  {
    "district": "Bikaner",
    "state": "Rajasthan",
    "pincode": "334001",
    "aliases": [
      "bikaner"
    ]
  },
  {
    "district": "Bundi",
    "state": "Rajasthan",
    "pincode": "323001",
    "aliases": [
      "bundi"
    ]
  },
  {
    "district": "Chittorgarh",
    "state": "Rajasthan",
    "pincode": "312001",
    "aliases": [
      "chittorgarh"
    ]
  },
  {
    "district": "Churu",
    "state": "Rajasthan",
    "pincode": "331001",
    "aliases": [
      "churu"
    ]
  },
  {
    "district": "Dausa",
    "state": "Rajasthan",
    "pincode": "303303",
    "aliases": [
      "dausa"
    ]
  },
  {
    "district": "Dholpur",
    "state": "Rajasthan",
    "pincode": "328001",
    "aliases": [
      "dholpur"
    ]
  },
  {
    "district": "Dungarpur",
    "state": "Rajasthan",
    "pincode": "314001",
    "aliases": [
      "dungarpur"
    ]
  },
  {
    "district": "Hanumangarh",
    "state": "Rajasthan",
    "pincode": "335512",
    "aliases": [
      "hanumangarh"
    ]
  },
  {
    "district": "Jaipur",
    "state": "Rajasthan",
    "pincode": "302001",
    "aliases": [
      "jaipur"
    ]
  },
  {
    "district": "Jaisalmer",
    "state": "Rajasthan",
    "pincode": "345001",
    "aliases": [
      "jaisalmer"
    ]
  },
  {
    "district": "Jalore",
    "state": "Rajasthan",
    "pincode": "343001",
    "aliases": [
      "jalore"
    ]
  },
  {
    "district": "Jhalawar",
    "state": "Rajasthan",
    "pincode": "326001",
    "aliases": [
      "jhalawar"
    ]
  },
  {
    "district": "Jhunjhunu",
    "state": "Rajasthan",
    "pincode": "333001",
    "aliases": [
      "jhunjhunu"
    ]
  },
  {
    "district": "Jodhpur",
    "state": "Rajasthan",
    "pincode": "342001",
    "aliases": [
      "jodhpur"
    ]
  },
  {
    "district": "Karauli",
    "state": "Rajasthan",
    "pincode": "322241",
    "aliases": [
      "karauli"
    ]
  },
  {
    "district": "Kota",
    "state": "Rajasthan",
    "pincode": "324001",
    "aliases": [
      "kota"
    ]
  },
  {
    "district": "Nagaur",
    "state": "Rajasthan",
    "pincode": "341001",
    "aliases": [
      "nagaur"
    ]
  },
  {
    "district": "Pali",
    "state": "Rajasthan",
    "pincode": "306401",
    "aliases": [
      "pali"
    ]
  },
  {
    "district": "Pratapgarh",
    "state": "Rajasthan",
    "pincode": "312605",
    "aliases": [
      "pratapgarh"
    ]
  },
  {
    "district": "Rajsamand",
    "state": "Rajasthan",
    "pincode": "313324",
    "aliases": [
      "rajsamand"
    ]
  },
  {
    "district": "Sawai Madhopur",
    "state": "Rajasthan",
    "pincode": "322001",
    "aliases": [
      "sawai madhopur"
    ]
  },
  {
    "district": "Sikar",
    "state": "Rajasthan",
    "pincode": "332001",
    "aliases": [
      "sikar"
    ]
  },
  {
    "district": "Sirohi",
    "state": "Rajasthan",
    "pincode": "307001",
    "aliases": [
      "sirohi"
    ]
  },
  {
    "district": "Sri Ganganagar",
    "state": "Rajasthan",
    "pincode": "335001",
    "aliases": [
      "sri ganganagar",
      "ganganagar"
    ]
  },
  {
    "district": "Tonk",
    "state": "Rajasthan",
    "pincode": "304001",
    "aliases": [
      "tonk"
    ]
  },
  {
    "district": "Udaipur",
    "state": "Rajasthan",
    "pincode": "313001",
    "aliases": [
      "udaipur"
    ]
  },
  {
    "district": "Agra",
    "state": "Uttar Pradesh",
    "pincode": "282001",
    "aliases": [
      "agra"
    ]
  },
  {
    "district": "Aligarh",
    "state": "Uttar Pradesh",
    "pincode": "202001",
    "aliases": [
      "aligarh"
    ]
  },
  {
    "district": "Ayodhya",
    "state": "Uttar Pradesh",
    "pincode": "224123",
    "aliases": [
      "ayodhya",
      "faizabad"
    ]
  },
  {
    "district": "Bareilly",
    "state": "Uttar Pradesh",
    "pincode": "243001",
    "aliases": [
      "bareilly"
    ]
  },
  {
    "district": "Firozabad",
    "state": "Uttar Pradesh",
    "pincode": "283203",
    "aliases": [
      "firozabad"
    ]
  },
  {
    "district": "Gautam Buddha Nagar",
    "state": "Uttar Pradesh",
    "pincode": "201301",
    "aliases": [
      "gautam buddha nagar",
      "noida",
      "greater noida"
    ]
  },
  {
    "district": "Ghaziabad",
    "state": "Uttar Pradesh",
    "pincode": "201001",
    "aliases": [
      "ghaziabad"
    ]
  },
  {
    "district": "Gorakhpur",
    "state": "Uttar Pradesh",
    "pincode": "273001",
    "aliases": [
      "gorakhpur"
    ]
  },
  {
    "district": "Jhansi",
    "state": "Uttar Pradesh",
    "pincode": "284001",
    "aliases": [
      "jhansi"
    ]
  },
  {
    "district": "Kanpur Nagar",
    "state": "Uttar Pradesh",
    "pincode": "208001",
    "aliases": [
      "kanpur",
      "kanpur nagar"
    ]
  },
  {
    "district": "Lucknow",
    "state": "Uttar Pradesh",
    "pincode": "226001",
    "aliases": [
      "lucknow"
    ]
  },
  {
    "district": "Mathura",
    "state": "Uttar Pradesh",
    "pincode": "281001",
    "aliases": [
      "mathura"
    ]
  },
  {
    "district": "Meerut",
    "state": "Uttar Pradesh",
    "pincode": "250001",
    "aliases": [
      "meerut"
    ]
  },
  {
    "district": "Moradabad",
    "state": "Uttar Pradesh",
    "pincode": "244001",
    "aliases": [
      "moradabad"
    ]
  },
  {
    "district": "Muzaffarnagar",
    "state": "Uttar Pradesh",
    "pincode": "251001",
    "aliases": [
      "muzaffarnagar"
    ]
  },
  {
    "district": "Prayagraj",
    "state": "Uttar Pradesh",
    "pincode": "211001",
    "aliases": [
      "prayagraj",
      "allahabad"
    ]
  },
  {
    "district": "Saharanpur",
    "state": "Uttar Pradesh",
    "pincode": "247001",
    "aliases": [
      "saharanpur"
    ]
  },
  {
    "district": "Varanasi",
    "state": "Uttar Pradesh",
    "pincode": "221001",
    "aliases": [
      "varanasi",
      "banaras",
      "kashi"
    ]
  },
  {
    "district": "Kolkata",
    "state": "West Bengal",
    "pincode": "700001",
    "aliases": [
      "kolkata",
      "calcutta"
    ]
  },
  {
    "district": "Howrah",
    "state": "West Bengal",
    "pincode": "711101",
    "aliases": [
      "howrah"
    ]
  },
  {
    "district": "North 24 Parganas",
    "state": "West Bengal",
    "pincode": "700124",
    "aliases": [
      "north 24 parganas",
      "barasat"
    ]
  },
  {
    "district": "South 24 Parganas",
    "state": "West Bengal",
    "pincode": "743329",
    "aliases": [
      "south 24 parganas",
      "alipore"
    ]
  },
  {
    "district": "Hooghly",
    "state": "West Bengal",
    "pincode": "712101",
    "aliases": [
      "hooghly",
      "chinsurah"
    ]
  },
  {
    "district": "Darjeeling",
    "state": "West Bengal",
    "pincode": "734101",
    "aliases": [
      "darjeeling",
      "siliguri"
    ]
  },
  {
    "district": "Paschim Bardhaman",
    "state": "West Bengal",
    "pincode": "713301",
    "aliases": [
      "asansol",
      "durgapur",
      "bardhaman"
    ]
  },
  {
    "district": "Patna",
    "state": "Bihar",
    "pincode": "800001",
    "aliases": [
      "patna"
    ]
  },
  {
    "district": "Gaya",
    "state": "Bihar",
    "pincode": "823001",
    "aliases": [
      "gaya"
    ]
  },
  {
    "district": "Bhagalpur",
    "state": "Bihar",
    "pincode": "812001",
    "aliases": [
      "bhagalpur"
    ]
  },
  {
    "district": "Muzaffarpur",
    "state": "Bihar",
    "pincode": "842001",
    "aliases": [
      "muzaffarpur"
    ]
  },
  {
    "district": "Darbhanga",
    "state": "Bihar",
    "pincode": "846004",
    "aliases": [
      "darbhanga"
    ]
  },
  {
    "district": "Bhopal",
    "state": "Madhya Pradesh",
    "pincode": "462001",
    "aliases": [
      "bhopal"
    ]
  },
  {
    "district": "Indore",
    "state": "Madhya Pradesh",
    "pincode": "452001",
    "aliases": [
      "indore"
    ]
  },
  {
    "district": "Jabalpur",
    "state": "Madhya Pradesh",
    "pincode": "482001",
    "aliases": [
      "jabalpur"
    ]
  },
  {
    "district": "Gwalior",
    "state": "Madhya Pradesh",
    "pincode": "474001",
    "aliases": [
      "gwalior"
    ]
  },
  {
    "district": "Ujjain",
    "state": "Madhya Pradesh",
    "pincode": "456001",
    "aliases": [
      "ujjain"
    ]
  },
  {
    "district": "Amritsar",
    "state": "Punjab",
    "pincode": "143001",
    "aliases": [
      "amritsar"
    ]
  },
  {
    "district": "Ludhiana",
    "state": "Punjab",
    "pincode": "141001",
    "aliases": [
      "ludhiana"
    ]
  },
  {
    "district": "Jalandhar",
    "state": "Punjab",
    "pincode": "144001",
    "aliases": [
      "jalandhar"
    ]
  },
  {
    "district": "SAS Nagar",
    "state": "Punjab",
    "pincode": "160055",
    "aliases": [
      "sas nagar",
      "mohali"
    ]
  },
  {
    "district": "Gurugram",
    "state": "Haryana",
    "pincode": "122001",
    "aliases": [
      "gurugram",
      "gurgaon"
    ]
  },
  {
    "district": "Faridabad",
    "state": "Haryana",
    "pincode": "121001",
    "aliases": [
      "faridabad"
    ]
  },
  {
    "district": "Panipat",
    "state": "Haryana",
    "pincode": "132103",
    "aliases": [
      "panipat"
    ]
  },
  {
    "district": "Panchkula",
    "state": "Haryana",
    "pincode": "134109",
    "aliases": [
      "panchkula"
    ]
  },
  {
    "district": "Chandigarh",
    "state": "Chandigarh",
    "pincode": "160017",
    "aliases": [
      "chandigarh"
    ]
  },
  {
    "district": "Khordha",
    "state": "Odisha",
    "pincode": "751001",
    "aliases": [
      "khordha",
      "bhubaneswar"
    ]
  },
  {
    "district": "Cuttack",
    "state": "Odisha",
    "pincode": "753001",
    "aliases": [
      "cuttack"
    ]
  },
  {
    "district": "Kamrup Metropolitan",
    "state": "Assam",
    "pincode": "781001",
    "aliases": [
      "guwahati",
      "kamrup"
    ]
  },
  {
    "district": "North Goa",
    "state": "Goa",
    "pincode": "403001",
    "aliases": [
      "panaji",
      "north goa"
    ]
  },
  {
    "district": "South Goa",
    "state": "Goa",
    "pincode": "403601",
    "aliases": [
      "margao",
      "south goa"
    ]
  },
  {
    "district": "Puducherry",
    "state": "Puducherry",
    "pincode": "605001",
    "aliases": [
      "puducherry",
      "pondicherry"
    ]
  },
  {
    "district": "Srinagar",
    "state": "Jammu & Kashmir",
    "pincode": "190001",
    "aliases": [
      "srinagar"
    ]
  },
  {
    "district": "Jammu",
    "state": "Jammu & Kashmir",
    "pincode": "180001",
    "aliases": [
      "jammu"
    ]
  },
  {
    "district": "Ranchi",
    "state": "Jharkhand",
    "pincode": "834001",
    "aliases": [
      "ranchi"
    ]
  },
  {
    "district": "Jamshedpur",
    "state": "Jharkhand",
    "pincode": "831001",
    "aliases": [
      "jamshedpur",
      "east singhbhum"
    ]
  },
  {
    "district": "Raipur",
    "state": "Chhattisgarh",
    "pincode": "492001",
    "aliases": [
      "raipur"
    ]
  },
  {
    "district": "Dehradun",
    "state": "Uttarakhand",
    "pincode": "248001",
    "aliases": [
      "dehradun"
    ]
  },
  {
    "district": "Shimla",
    "state": "Himachal Pradesh",
    "pincode": "171001",
    "aliases": [
      "shimla"
    ]
  }
];


// Helper function to find location by district query (fuzzy / case-insensitive)
function findLocationByDistrict(query) {
  if (!query || typeof query !== 'string') return null;
  const clean = query.trim().toLowerCase().replace(/[^a-z0-9]/g, '');
  if (!clean || clean.length < 2) return null;

  // 1. Exact district name match
  let match = INDIA_LOCATIONS.find(loc => {
    const locClean = loc.district.toLowerCase().replace(/[^a-z0-9]/g, '');
    return locClean === clean;
  });
  if (match) return match;

  // 2. Exact alias match
  match = INDIA_LOCATIONS.find(loc => {
    return loc.aliases.some(a => a.toLowerCase().replace(/[^a-z0-9]/g, '') === clean);
  });
  if (match) return match;

  // 3. Starts with match
  match = INDIA_LOCATIONS.find(loc => {
    const locClean = loc.district.toLowerCase().replace(/[^a-z0-9]/g, '');
    return locClean.startsWith(clean);
  });
  if (match) return match;

  // 4. Alias starts with
  match = INDIA_LOCATIONS.find(loc => {
    return loc.aliases.some(a => a.toLowerCase().replace(/[^a-z0-9]/g, '').startsWith(clean));
  });
  if (match) return match;

  // 5. Contains substring
  match = INDIA_LOCATIONS.find(loc => {
    const locClean = loc.district.toLowerCase().replace(/[^a-z0-9]/g, '');
    return locClean.includes(clean);
  });
  return match || null;
}

// Helper function to find location by PIN code
function findLocationByPincode(pincode) {
  if (!pincode || typeof pincode !== 'string') return null;
  const digits = pincode.trim().replace(/\D/g, '');
  if (digits.length < 3) return null;

  // 1. Exact 6-digit match
  let match = INDIA_LOCATIONS.find(loc => loc.pincode === digits);
  if (match) return match;

  // 2. Prefix match (first 3 digits indicate postal division)
  if (digits.length >= 3) {
    const prefix = digits.substring(0, 3);
    match = INDIA_LOCATIONS.find(loc => loc.pincode.startsWith(prefix));
    if (match) return match;
  }
  return null;
}

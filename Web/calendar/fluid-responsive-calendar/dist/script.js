// ===================================================================
// 파베 부분


// src='https://cdn.firebase.com/js/client/2.2.1/firebase.js'
// src='https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js'


src="https://www.gstatic.com/firebasejs/4.11.0/firebase.js"
var config = {
  apiKey: "AIzaSyCWKAgyNFV22IpW5EA9MfOBhV6MHOpL7PI",
  authDomain: "uume-58fe8.firebaseapp.com",
  databaseURL: "https://uume-58fe8-default-rtdb.firebaseio.com",
  projectId: "uume-58fe8",
  storageBucket: "uume-58fe8.appspot.com",
  messagingSenderId: "1022617126475",
  appId: "1:1022617126475:web:0569a1422385e31debefce",
  measurementId: "${config.measurementId}"
};
firebase.initializeApp(config);         

//var id_Field = document.getElementById("id");
//var password_Field = document.getElementById("password");

var database = firebase.database();

function readdata() {
  //var id = id_Field.value;
  //var password = password_Field.value;
  // var fase_closer = 'face_closer' 
  // var dbTestRef = database.ref('class/seojin915/20220509/scienceA/minsu306/');
  const dbTestRef = ref(db, 'class/seojin915/20220509/scienceA/minsu306');
  dbTestRef.on('child_added', function(data){
    // alert(id + password);
    console.log(data.val().face_cloaser);
      
    


    
  })



}

// ===================================================================
// Our labels along the x-axis
var years = [1500,1600,1700,1750,1800,1850,1900,1950,1999,2050];
// For drawing the lines
readdata();
var africa = [86,114,106,106,107,111,133,221,783,2478];
var asia = [282,350,411,502,635,809,947,1402,3700,5267];
var europe = [168,170,178,190,203,276,408,547,675,734];
var latinAmerica = [40,20,10,16,24,38,74,167,508,784];
var northAmerica = [6,3,2,2,7,26,82,172,312,433];

var ctx = document.getElementById("myChart");
var myChart = new Chart(ctx, {
  type: 'pie',
  data: {
    labels: ["Africa", "Asia", "Europe", "Latin America", "North America"],
    datasets: [{
      label: "Population (millions)",
      backgroundColor: ["#3e95cd", "#8e5ea2","#3cba9f","#e8c3b9","#c45850"],
      data: [2478,5267,734,784,433]
    }]
  },
  options: {
    title: {
      display: true,
      text: 'Predicted world population (millions) in 2050'
    }
  }
});
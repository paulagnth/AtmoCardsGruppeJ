let context = new AudioContext();
let sounds = [];
let soundNodes = [];
let gains = [] 
let pans = []
let anzahl_sample = 9;

let masterGain = context.createGain();
let convolver = context.createConvolver();

let playstop = document.querySelector('#startButton');
let isPlaying = true;
let hall_button = document.querySelector('#hall_button')
let hall_on_off = false;

let WebCamElement = document.getElementById('VideoElement');
let webcam = new Webcam(WebCamElement, 'user');
let webcam_button = document.querySelector('#webcam_button');
let webcam_on_off = false;


masterGain.gain.value = 1;


// Webcam Einbindung
webcam_button.addEventListener('click', function(e){
    if(webcam_on_off){
        webcam_button.innerHTML = 'Webcam On';
        webcam.start();
    }else{
        webcam_button.innerHTML = 'Webcam Off';
        webcam.stop();
    }
    webcam_on_off = !webcam_on_off;
});

document.querySelector('#gainSlider').addEventListener('input', function(e) {
    let masterGain_value = this.value/100;
    masterGain.gain.value = masterGain_value;
});
// Reverb über Button 
hall_button.addEventListener('click', function(e){
    if (hall_on_off){
        convolver.disconnect(context.destination);
        masterGain.connect(context.destination);
        hall_button.innerHTML = 'Reverb On'
    }else{
        impulsAntworten('room');
        convolver.connect(masterGain);
        masterGain.connect(context.destination);
        hall_button.innerHTML = 'Reverb Off'
        document.querySelector('#select_reverb').addEventListener('change', function (e) {
            let name = e.target.options[e.target.selectedIndex].value;
            impulsAntworten(name);
        });  
    }
    hall_on_off = !hall_on_off;

});


// Schleife über Anzahl der Samples 
 
for (let i = 0; i < anzahl_sample; i++) {
    sounds[i] = new Audio('/sounds/sound' + (i + 1) + '.wav'); // Samples aus Unterordner 'sounds' laden
    soundNodes[i] = context.createMediaElementSource(sounds[i]);
    gains[i] = context.createGain(); // Gain-Node erstellen
    pans[i] = context.createStereoPanner(); //Pan-Node erstellen
    // Audiograph pro Sample zusammenstecken
    soundNodes[i].connect(gains[i]);
    gains[i].connect(pans[i]);
    pans[i].connect(masterGain);
    //masterGain.connect(context.destination);
 
} 
// Start/ Stop Button
playstop.addEventListener('click', function(e){
    if(isPlaying){
        playstop.innerHTML = 'Stop';
        masterGain.connect(context.destination);
    } else{
        playstop.innerHTML = 'Start';
        masterGain.disconnect(context.destination);
        if (convolver) {convolver.disconnect();};
    }
    isPlaying = !isPlaying;
});



// Sample abspielen 
function playSound(sample, velocity){ // Eingang: Sample Nr, Anschlagsstärke
    
    gains[sample-1].gain.value = velocity/127; // Gain abh von eingehener Anschlagsstärke setzen
    sounds[sample-1].loop = true; // Sample loopen
    sounds[sample-1].play(); // Sample abspielen
}
// Sample abspielen stoppen
function stopSound(sample, velocity){ // Eingang: Sample Nr, Anschlagsstärke (redundant strukturbedingt aufgeführt)
    sounds[sample-1].pause(); // Sample pausieren
}
// gain der Samples anpassen
function gainControl(sample, value) { // Eingang: Sample Nr, Gain Value in Midi-Wertebereich abh von y-Koordinate
    gains[sample-1].gain.value = value/127; // gain-Wert setzen auf Wertebereich der Gain-Node mappen
}
// panning der Samples anpassen
function panControl(sample, value) { // Eingang: Sample Nr, Pan Value in Midi-Wertebereich abh von x-Koordinate
    pans[sample-1].pan.value = ((value - 64) / 64); // pan-Wert setzen auf Werte-Bereich der Panner-Node mappen
}
// Impulsantworten für Reverb einlesen
function impulsAntworten(name) {
    fetch('/impulsAntworten/' + name + '.wav')
        .then(response => response.arrayBuffer())
        .then(undecodedAudio => context.decodeAudioData(undecodedAudio))
        .then(audioBuffer => {
            if (convolver) {convolver.disconnect();}

            convolver = context.createConvolver();
            convolver.buffer = audioBuffer;
            convolver.normalize = true;

            masterGain.connect(convolver);
            convolver.connect(context.destination);
        })
        .catch(console.error);
}


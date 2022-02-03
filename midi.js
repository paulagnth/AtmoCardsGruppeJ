if (navigator.requestMIDIAccess) {
    navigator.requestMIDIAccess({sysex: false}).then(function (midiAccess) {
        midi = midiAccess;
        var inputs = midi.inputs.values();
        // loop über alle Inputs
        for (var input = inputs.next(); input && !input.done; input = inputs.next()) {
            input.value.onmidimessage = onMIDIMessage; // onMidiMessage
        }
    });
} else {
    alert('No MIDI support in your browser.');
}

function onMIDIMessage(event) {
    switch (event.data[0]) {
        case 144:
            playSound(event.data[1], event.data[2]);
            break;
        case 128:
            stopSound(event.data[1], event.data[2]);
            break;
        case 160:
            gainControl(event.data[1], event.data[2]);
            break;
        case 176:
            panControl(event.data[1], event.data[2]);
            break;
        }

    
}
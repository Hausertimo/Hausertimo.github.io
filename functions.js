//todo 
//cns pns draw$
//Purpose of Page: Easy & understandable yet deep and detailed knowledge over Brain. Prep for Uni.
var innercontent =
[
'<div class="textbox_left"> <div class="subb_titel">CNS/PNS</div>We disinguish between CNS(Central nervous system) and PNS(Peripheral nervous system).<br> <br></div><div class="textbox_left"><div class="subb_titel">CNS</div> <br> The Central nervous system Includes the Brainstem, Cerebrum, Cerebellum and Spinal cord. <br> <br>Cerebrum <br>On Avarage brain messures 3 pounds (1.3kg) of which 60% is fat and and the remaining parts are water, protein, carbohydrates and salts. <br>Largest brain part composed of Left & Right Hemisphere. <br>Function: Higher <br>Example: Interpretation of touch, sight, speech, thought <br><br>Cerebellum <br>Located under Cerebrum <br>Function: Movement, Coordinationbr <br>Example: Kicking soccer ball <br> <br></div><div  class="textbox_left"><div class="subb_titel">PNS</div>The Peripheral nervous system includes all Nerves leading threwout the Body wit the exclussion of the Central nervous system. <br><br></div><div id="content_1" class="empty">',
'<div  class="textbox_left"><div class="subb_titel">LEFT & RIGHT</div><br>The Brain has two Hemispheres. They are connected by the corpus collosum. <br><br>Corpus collosum is a bundle of fibers that transmit messages from one side to the other. <br><br>The hemisphere controls the opposite side of the body. <br> <br>Not all functions are executed on both sides. <br> <br>L: Speech, comprehension, arithmetic, writing <br> <br>R: Creativity spatial ability, artistic, musical skill <br> <br> The left hemisphere is dominant in hand use in roughly 92% of people<br><br></div></div> <div  class="textbox_left"> <div class="subb_titel">Corpus Collosum</div> <br> Both Sides are in constant exchange. Mainly over the Corpuscollosum <br> Corpus Collosum are over million nerve fibers <br> <br> </div>',
'<div id="content_2" class="empty">      <div class="textbox_left"><div class="subb_titel">LOBES <br> <br> </div></div><div class="textbox_left"><div class="subb_titel"> Parietal Lobe</div> <br>    -Interpreting Language, words<br>    -Sense of touch, pain, temperature (sensory strip)<br>    -interpretation of signals from vision, hearing, motor. Sensory and memory<br>    -spatial and visual perception    <br> <br></div> <div class="textbox_left">    <div class="subb_titel">Frontal Lobe</div> <br>    -personality, behavior, emotions<br>    -Judgment, planning, problem solving<br>    -Speech: speaking and writing (Broca area)<br>    -Body movement (motor strip)<br>    -Intelligence, concentration, self awareness<br><br>    </div> <div class="textbox_left">    <div class="subb_titel">Occipital lobe</div> <br>    -Interprets vision like color, light, movement      <br> <br></div> <div class="textbox_left">    <div class="subb_titel">Temporal Lobe</div> <br>    -Understanding language (wernicks Area)<br>    -Memory<br>    -Hearing <br>    -Sequencing <br> <br></div>',
'1']


function navigation(i){
    

    const box = document.getElementById("content_"+i);

    if (box.childNodes.length === 0) {
    document.getElementById("content_"+i).innerHTML= innercontent[i];
    document.getElementById("pic_"+i).style.opacity = 0.3;
    } else {
    document.getElementById("content_"+i).innerHTML = "";
    document.getElementById("pic_"+i).style.opacity = 1;
    }

};

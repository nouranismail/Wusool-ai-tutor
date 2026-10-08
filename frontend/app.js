// Wusool front end. Plain JavaScript, no build step.

const state = {
  mode: null,
  subject: null,
  lessons: [],
  lesson: null,
  language: "ar",
  questionIndex: 0,
  lessonStep: 0,
  group: { socket: null, role: null, name: null, code: null, hostToken: null, current: null },
};

const $ = (id) => document.getElementById(id);
const panels = ["welcome", "subjects", "lessons", "lesson", "group"];

function show(id) {
  panels.forEach((name) => $(name).classList.toggle("hidden", name !== id));
  $(id).setAttribute("tabindex", "-1");
  $(id).focus();
}

// ---------- Speech ----------

function speak(text, onEnd) {
  if (!("speechSynthesis" in window)) {
    onEnd?.();
    return;
  }
  speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = state.language === "ar" ? "ar-SA" : "en-US";
  utterance.rate = 0.88;
  utterance.onend = () => onEnd?.();
  speechSynthesis.speak(utterance);
}

function voiceStatus(text, on = true) {
  $("voice-status").textContent = text;
  $("voice-status").classList.toggle("active", on);
  if (on) setTimeout(() => voiceStatus("", false), 3500);
}

function listen(callback) {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    voiceStatus("التعرف على الصوت غير مدعوم. استخدم الأزرار أو الكتابة.");
    return;
  }
  const recognition = new Recognition();
  recognition.lang = state.language === "ar" ? "ar-EG" : "en-US";
  recognition.interimResults = false;
  recognition.onstart = () => voiceStatus("أستمع إليك الآن…");
  recognition.onerror = (event) =>
    voiceStatus(
      event.error === "not-allowed"
        ? "اسمح للمتصفح باستخدام الميكروفون ثم حاول مرة أخرى."
        : "لم أسمع بوضوح. حاول مرة أخرى."
    );
  recognition.onresult = (event) => callback(event.results[0][0].transcript);
  recognition.start();
}

// ---------- Access mode and subject ----------

function listenForSubject() {
  listen((text) => {
    if (/رياض|حساب|math/i.test(text)) chooseSubject("math");
    else if (/حاسب|كمبيوتر|ict/i.test(text)) chooseSubject("ict");
    else speak("لم أفهم الاختيار. قل رياضيات أو أساسيات كمبيوتر.", listenForSubject);
  });
}

function promptForSubject() {
  speak("هل تريد الرياضيات أم أساسيات الكمبيوتر؟ قل اختيارك بعد سماع الرسالة.", listenForSubject);
}

document.querySelectorAll("[data-mode]").forEach((button) =>
  button.addEventListener("click", () => {
    state.mode = button.dataset.mode;
    document.body.className = `mode-${state.mode}`;
    show("subjects");
    if (state.mode === "vision") promptForSubject();
    else speak("اختر الرياضيات أو أساسيات الكمبيوتر");
  })
);

// ---------- Lesson list ----------

const ORDINALS = [
  /أول|اول|واحد|one|first/i,
  /ثاني|ثانى|اثنين|اتنين|two|second/i,
  /ثالث|ثلاثة|تلاتة|three|third/i,
  /رابع|أربعة|اربعة|four/i,
  /خامس|خمسة|five/i,
  /سادس|ستة|six/i,
  /سابع|سبعة|seven/i,
  /ثامن|ثمانية|eight/i,
  /تاسع|تسعة|nine/i,
  /عاشر|عشرة|ten/i,
];

function lessonTitle(lesson) {
  return state.language === "ar" ? lesson.title_ar : lesson.title_en;
}

function renderLessonList() {
  const list = $("lesson-list");
  list.replaceChildren(
    ...state.lessons.map((lesson, index) => {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.lessonId = lesson.id;

      const number = document.createElement("span");
      number.className = "lesson-number";
      number.setAttribute("aria-hidden", "true");
      number.textContent = String(index + 1);

      const title = document.createElement("span");
      title.textContent = `الدرس ${index + 1}: ${lessonTitle(lesson)}`;
      if (state.language === "en") title.textContent = `Lesson ${index + 1}: ${lessonTitle(lesson)}`;

      button.append(number, title);
      if (lesson.review_status !== "approved") {
        const status = document.createElement("span");
        status.className = "lesson-status";
        status.textContent = state.language === "ar" ? "قيد المراجعة" : "Under review";
        button.append(status);
      }
      button.addEventListener("click", () => chooseLesson(lesson.id));
      item.append(button);
      return item;
    })
  );
}

function announceLessons(thenListen) {
  const spoken = state.lessons.map((lesson, index) => `الدرس ${index + 1}: ${lesson.title_ar}.`).join(" ");
  speak(`اختر الدرس. ${spoken}`, thenListen ? listenForLesson : undefined);
}

function listenForLesson() {
  listen((text) => {
    const digits = text.replace(/[٠-٩]/g, (d) => "٠١٢٣٤٥٦٧٨٩".indexOf(d));
    const number = digits.match(/\d+/);
    let index = number ? Number(number[0]) - 1 : ORDINALS.findIndex((pattern) => pattern.test(text));
    if (!(index >= 0 && index < state.lessons.length)) {
      const byTitle = state.lessons.findIndex((lesson) => text.includes(lesson.title_ar));
      index = byTitle;
    }
    if (index >= 0 && index < state.lessons.length) chooseLesson(state.lessons[index].id);
    else speak("لم أفهم رقم الدرس. قل مثلًا: الدرس الأول.", listenForLesson);
  });
}

async function chooseSubject(subject) {
  state.subject = subject;
  const response = await fetch(`/api/lessons?subject=${encodeURIComponent(subject)}`);
  if (!response.ok) {
    voiceStatus("تعذر تحميل الدروس");
    return;
  }
  state.lessons = await response.json();
  renderLessonList();
  show("lessons");
  if (state.mode === "vision") announceLessons(true);
  else speak("اختر الدرس.");
}

async function chooseLesson(lessonId) {
  const chosen = state.lessons.find((lesson) => lesson.id === lessonId);
  const response = await fetch("/api/tutor", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      subject: state.subject,
      query: chosen ? chosen.title_ar : lessonId,
      language: state.language,
      lesson_id: lessonId,
    }),
  });
  if (!response.ok) {
    voiceStatus("تعذر تحميل الدرس");
    return;
  }
  state.lesson = await response.json();
  state.lessonStep = 0;
  state.questionIndex = 0;
  $("lesson-title").textContent = state.lesson.title;
  $("lesson-source").textContent =
    state.lesson.review_status === "approved" ? "من المنهج المعتمد" : "نسخة محتوى قيد مراجعة المعلم";
  $("start-question").classList.add("hidden");
  $("create-group").classList.add("hidden");
  $("question-box").classList.add("hidden");
  $("feedback").textContent = "";
  show("lesson");
  playLesson();
}

function backToLessons() {
  if ("speechSynthesis" in window) speechSynthesis.cancel();
  show("lessons");
}

// ---------- Lesson and individual practice ----------

function playLesson() {
  const steps = state.lesson.lesson_steps || [state.lesson.explanation];
  const play = (index) => {
    state.lessonStep = index;
    $("lesson-text").textContent = steps[index];
    speak(steps[index], () => {
      if (index + 1 < steps.length) play(index + 1);
      else finishLesson();
    });
  };
  play(0);
}

function finishLesson() {
  const message = "انتهى شرح الدرس. هل تريد التدريب بمفردك أم إنشاء جلسة جماعية؟";
  $("lesson-text").textContent += `\n\n${message}`;
  $("start-question").classList.remove("hidden");
  $("create-group").classList.remove("hidden");
  speak(message);
}

function currentQuestion() {
  return state.lesson.questions[state.questionIndex];
}

function beginIndividual() {
  const question = currentQuestion();
  $("question-box").classList.remove("hidden");
  $("question").textContent = question.text;
  $("answer").value = "";
  $("feedback").textContent = "";
  speak(question.text);
  $("answer").focus();
}

async function submitAnswer() {
  const value = $("answer").value.trim();
  if (!value) {
    voiceStatus("من فضلك قل أو اكتب إجابتك");
    return;
  }
  const question = currentQuestion();
  const response = await fetch("/api/answer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lesson_id: state.lesson.lesson_id, question_id: question.id, answer: value }),
  });
  if (!response.ok) {
    voiceStatus("تعذر فحص الإجابة");
    return;
  }
  const result = await response.json();
  const feedback = state.language === "ar" ? result.feedback_ar : result.feedback_en;
  $("feedback").textContent = feedback;
  speak(feedback, () => {
    if (result.correct && state.questionIndex + 1 < state.lesson.questions.length) {
      state.questionIndex++;
      beginIndividual();
    } else if (result.correct) {
      speak("أكملت أسئلة الدرس. أحسنت!");
    }
  });
}

document.querySelectorAll("[data-subject]").forEach((button) =>
  button.addEventListener("click", () => chooseSubject(button.dataset.subject))
);
$("listen-subject").addEventListener("click", listenForSubject);
$("listen-lesson").addEventListener("click", listenForLesson);
$("back-to-subjects").addEventListener("click", () => {
  if ("speechSynthesis" in window) speechSynthesis.cancel();
  show("subjects");
});
$("back-to-lessons").addEventListener("click", backToLessons);
$("speak-lesson").addEventListener("click", playLesson);
$("start-question").addEventListener("click", beginIndividual);
$("listen-answer").addEventListener("click", () =>
  listen((text) => {
    $("answer").value = text;
    voiceStatus(`سمعت: ${text}`);
  })
);
$("submit-answer").addEventListener("click", submitAnswer);

// ---------- Group session ----------

function wsUrl(code, name, role, token = "") {
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://${location.host}/ws/group/${code}?name=${encodeURIComponent(name)}&role=${role}&token=${encodeURIComponent(token)}`;
}

function connectGroup(code, name, role, token = "") {
  state.group = { socket: new WebSocket(wsUrl(code, name, role, token)), role, name, code, hostToken: token, current: null };
  $("group-join-form").classList.add("hidden");
  $("group-room").classList.remove("hidden");
  $("room-code-display").textContent = code;
  if (role === "host") $("start-group").classList.remove("hidden");
  state.group.socket.onmessage = (event) => handleGroupMessage(JSON.parse(event.data));
  state.group.socket.onerror = () => voiceStatus("تعذر الاتصال بالغرفة");
  state.group.socket.onclose = () => {
    $("group-status").textContent = "انقطع الاتصال بالغرفة.";
  };
}

function renderParticipants(message) {
  // Nicknames come from other children, so they are always inserted as plain text, never as HTML.
  $("participants").replaceChildren(
    ...message.participants.map((name) => {
      const item = document.createElement("li");
      item.textContent = name;
      item.classList.toggle("current-turn", name === message.current_participant);
      return item;
    })
  );
}

function handleGroupMessage(message) {
  if (message.type === "room_state") {
    renderParticipants(message);
    state.group.current = message.current_participant;
    $("group-status").textContent = message.active
      ? `الدور الآن على ${message.current_participant}`
      : "في انتظار بدء المعلم";
    return;
  }
  if (message.type === "question") {
    $("group-question-box").classList.toggle("hidden", state.group.role !== "participant");
    $("group-question").textContent = `سؤال ${message.participant}: ${message.text}`;
    const announcement = `الدور على ${message.participant}. ${message.text}`;
    speak(announcement, () => {
      if (state.mode === "vision" && state.group.name === message.participant) {
        listen((text) => {
          $("group-answer").value = text;
        });
      }
    });
    return;
  }
  if (message.type === "feedback" || message.type === "complete" || message.type === "error") {
    $("group-status").textContent = message.message;
    speak(message.message);
    if (message.type === "complete") $("group-question-box").classList.add("hidden");
  }
}

$("join-group-home").addEventListener("click", () => show("group"));

$("create-group").addEventListener("click", async () => {
  const response = await fetch("/api/group/rooms", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lesson_id: state.lesson.lesson_id }),
  });
  const room = await response.json();
  show("group");
  connectGroup(room.code, "المعلم", "host", room.host_token);
  speak(`تم إنشاء الغرفة. الرمز هو ${room.code.split("").join(" ")}`);
});

$("join-group").addEventListener("click", () => {
  const code = $("group-code").value.trim().toUpperCase();
  const name = $("participant-name").value.trim();
  if (!code || !name) {
    voiceStatus("أدخل رمز الغرفة والاسم المستعار");
    return;
  }
  connectGroup(code, name, "participant");
});

$("start-group").addEventListener("click", () => state.group.socket?.send(JSON.stringify({ type: "start" })));

$("group-listen-answer").addEventListener("click", () =>
  listen((text) => {
    $("group-answer").value = text;
  })
);

$("send-group-answer").addEventListener("click", () => {
  const answer = $("group-answer").value.trim();
  if (answer) state.group.socket?.send(JSON.stringify({ type: "answer", answer }));
});

// ---------- Language ----------

$("language").addEventListener("click", () => {
  state.language = state.language === "ar" ? "en" : "ar";
  document.documentElement.lang = state.language;
  document.documentElement.dir = state.language === "ar" ? "rtl" : "ltr";
  $("language").textContent = state.language === "ar" ? "English" : "العربية";
  if (state.lessons.length) renderLessonList();
  voiceStatus(state.language === "ar" ? "تم اختيار العربية" : "English selected");
});

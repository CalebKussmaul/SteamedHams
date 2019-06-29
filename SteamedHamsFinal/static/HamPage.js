var page = -1;
var minPage = 1;
var pageCount = 1956;

var maxSubSize = 1228800;

var userid = -1;
var isSuper = false;
var loggedIn = false;
var myVotes = {};
var checkingLogin = false;

var hamStrings = ["Well", "Seymour", "I", "made", "it", "despite", "your", "directions"];
var hamIndex = 1;
var submissions = [];
prevTop = null;
nextTop = null;
var topSub = null;
var origUrl = "https://steamedassets.nyc3.cdn.digitaloceanspaces.com/originals/frame";
var staticUrl = "https://steamedassets.nyc3.cdn.digitaloceanspaces.com/";
var htmlUrl = "https://obviouslygrilled.com/";

var musicTimeout = false;


$(document).ready(function() {
  clean(document);

  switch (getPageName()) {
    case "index":
      setupIndexPage();
      break;
    case "ham":
      setupHamPage();
      break;
    case "stat":
      setupStatPage();
      break;
    case "me":
      setupMePage();
      break;
    case "signup":
      setupSignupPage();
      break;
  }

  setInterval(function() {
    document.title = hamStrings[hamIndex];
    hamIndex = (hamIndex+1) % hamStrings.length;
  }, 1000);

  $(".borealis")[0].playbackRate = .3;

  if (!isMobile()) {
    $("#music").mouseover(function(e) {
      swapmusic();
    });
  }
  $("#music").on("touchstart", function(e) {
    swapmusic();
  });

  $(".underlay").text("steamed hams ".repeat(5000));

  $("#music").click(function(e) {playMusic();});
  $(".hamburger").click(function (e) {
    $(".hamburgerMenu").toggleClass("invisible");
  });

  $("#sortSelect").change(function (e) {
      refreshSubmissions();
  });

  $(document).mouseleave(function() {
    newsletter();
  });
  $("#stats").click(function () {
    loadPage("/statistics/", "/statistics/");
  });
  $("#home").click(function () {
    loadPage(htmlUrl + "Index.html", "/")
  });
  $("#in").click(function () {
    window.localStorage.setItem("redirect", window.location.href);
    loadPage(htmlUrl + "Signup.html", "/signup/")
  });
  $("#rules").click(function () {
    loadPage(htmlUrl + "Rules.html", "/rules/")
  });
  $("#me").click(function () {
    loadPage("/me/", "/me/")
  });
  $(".hamburgerLink").click(function () {
    $(".hamburgerMenu").addClass("invisible");
  });
  checkLogin();

  var msg = new URL(window.location).searchParams.get("msg");
  if (msg) {
    setTimeout(function () {
      window.alert(msg);
    }, 500);
  }
});

function swapmusic(){
  if(musicTimeout) {
    return;
  } else {
    musicTimeout = true;
    setTimeout(function () {musicTimeout = false}, 1000);
    $("#music").toggleClass("musicPos1").toggleClass("musicPos2");
  }
}

$(window).on('popstate', function (e) {
  location.reload(false);
});

function setupStatPage() {
  $(".frameLink").click(function (e) {
    loadHam($(this).attr("frameno"))
  });
}

function setupMePage() {
  $(".frameLink").click(function (e) {
    loadHam($(this).attr("frameno"))
  });
}

function setupSignupPage() {
  if (checkGrecaptcha()) {
    try {
      grecaptcha.render('cap1', {
        callback: function (response) {
          console.log(response);
        }
      });
    } catch (error) {
      console.error(error);
    }
  }
}

function setupHamPage() {
  page = parseInt(/(\/ham\/)?(\d+)\/?/g.exec(window.location.pathname)[2]);
  $("#next, .nextFrame").click(function () {
    page = Math.min(page + 1, pageCount);
    quickNext();
    navigate();
  });
  $("#prev, .prevFrame").click(function () {
    page = Math.max(page - 1, 1);
    quickPrev();
    navigate();
  });
  $(".modal-content").click(function (e) {
    e.originalEvent.stopPropagation();
  });
  $(".modal").click(function () {
    $(".modal").css('display', "none");
  });
  $('#transparency').on('input', function () {
    $('#modalComparison').css('opacity', $(this).val());
  });
  $('#subtract').on('change', function() {
    $('#modalComparison').toggleClass("subtract", $(this).checked);
  });

  $("#navForm").change(function () {
    page = parseInt($("#navForm").val());
    navigate();
  });
  $("#go").click(function () {
    page = Math.min(Math.max(parseInt($("#navForm").val()), 1), pageCount);
    navigate();
  });
  $("#rand").click(function () {
    page = Math.floor(Math.random() * (pageCount - 1) + 1);
    navigate();
  });

  $("#rules2").click(function () {
    loadPage(htmlUrl + "Rules.html", "/rules/")
  });
  $("#upload-login").click(function () {
    window.localStorage.setItem("redirect", window.location.href);
    loadPage(htmlUrl + "Signup.html", "/signup/")
  });

  $("#upload_btn").prop("disabled", true);

  $("#file").change(function () {
    if(validateSubmision()) {
      $(".cap2").show(500);
      $("#upload_btn").prop("disabled", false);
    }
  });

  $("#id_username").change(function () {
    if (validateSubmision()) {
      $(".cap1").show(500);
    }
  });

  //$("#submit").attr("action", "/ham/"+page+"/submit/");
  $("#submit").on("submit", function (event) {
    event.preventDefault();

    $.ajax({
      url: "/ham/" + page + "/submit/",
      method: "POST",
      processData: false,
      contentType: false,
      data: new FormData($("#submit")[0]),
      success: function (data) {
        window.alert("Submision accepted! (may take a few minutes to appear)");
      },
      error: handleError,
    }).always(function () {
      if(checkGrecaptcha()) {
        grecaptcha.reset();
      }
      $('#submit').trigger("reset");
      $('#upload_btn').attr("disabled", "disabled");
    });
  });
  checkLogin();
  navigate();

  if (checkGrecaptcha()) {
    try {
      grecaptcha.render('cap2', {
        callback: function (response) {
          console.log(response);
        }
      });
    } catch (error) {
      console.error(error);
    }
  }
}

function checkGrecaptcha() {
  return grecaptcha !== undefined && typeof grecaptcha.render === "function";
}

function checkLogin() {
  if(checkingLogin) {
    return;
  }
  if(loggedIn) {
    refreshLoginStuff();
  } else {
    checkingLogin = true;
    $.ajax({
      url: "/userinfo.json/",
      success: function (data) {
        checkingLogin = false;
        if (data["username"] !== undefined) {
          loggedIn = true;
          hamStrings[1] = data["username"];
          myVotes = data["uservotes"];
          userid = data["id"];
          isSuper = data["superuser"];
          refreshSubmissions();
        } else {
          loggedIn = false;
          hamStrings[1] = "Seymour";
        }
        refreshLoginStuff();
      },
      error: function (xhr, status, error) {
        checkingLogin = false;
        loggedIn = false;
        hamStrings[1] = "Seymour";
        refreshLoginStuff();
      }
    });
  }
}

function refreshLoginStuff() {
  console.log("logged in: "+loggedIn);
  if(loggedIn) {
    $("#in").addClass("invisible");
    $("#upload-form").removeClass("invisible");
    $("#upload-login").addClass("invisible");
    $("#me").removeClass("invisible");
  } else {
    $("#out").addClass("invisible");
    $("#upload-form").addClass("invisible");
    $("#upload-login").removeClass("invisible");
    $("#me").addClass("invisible");
  }
}

function validateSubmision() {
  var files = $("#file")[0].files;
  if(files.length === 0) {
    return false;
  }
  if (files[0].size > maxSubSize) {
    window.alert("File size too large");
    return false;
  }
  return true;
}

function setupIndexPage() {
  var redirect = window.localStorage.getItem("redirect");
  if (redirect) {
    window.localStorage.removeItem("redirect");
    window.location.href = redirect;
    return;
  }
  $("#enter").click(function () {
    loadHam(12);
  });
  checkLogin();
}

function navigate() {
  $.ajax({
    url: "/ham/" + page + "/cachable_submissions.json/",
    success: function (data) {
      submissions = data["submissions"];
      prevTop = data["prev-url"];
      nextTop = data["next-url"];
      window.history.replaceState(null, "", "/ham/" + page + "/");
      refreshSubmissions();
    },
    error: handleError,
  });
}

function quickNext() {
  $(".prevFrame").attr("src", $("#frame").attr("src"));
  $("#frame").attr("src", $(".nextFrame").attr("src"));
}

function quickPrev() {
  $(".nextFrame").attr("src", $("#frame").attr("src"));
  $("#frame").attr("src", $(".prevFrame").attr("src"));
}

function loadPage(url, pathOnly) {
  // if (pathOnly === "/signup/") {
  //   window.location.href = "/signup/";
  //   return;
  // }
  $.ajax({
    url: url,
    success: function (data) {
      //console.log("succ: " + data);
      window.history.replaceState(null, "", pathOnly);
      $("#wrap").replaceWith($(/.*<body>((.|\n)*)<\/body>.*/.exec(data)[0]).filter("#wrap"));
      if(pathOnly === "/") {
        setupIndexPage();
      } else if(pathOnly === "/statistics/") {
        setupStatPage();
      } else if (pathOnly === "/me/") {
        setupMePage();
      } else if (pathOnly === "/signup/") {
        setupSignupPage();
      }
    },
    error: handleError
  });
}

function loadHam(no) {
  if(getPageName() === "ham") {
    page = no;
    navigate();
  } else {
    $.ajax({
      url: htmlUrl + "HamPage.html",
      success: function (data) {
        window.history.pushState(null, "", "/ham/" + no + "/");
        $("#wrap").replaceWith($(/.*<body>((.|\n)*)<\/body>.*/.exec(data)[0]).filter("#wrap"));
        page = no;
        setupHamPage();
        playMusic();
      }
    });
  }
}


function refreshSubmissions() {

  $("#prev").toggle(page > minPage);
  $("#next").toggle(page < pageCount);

  $("#originallink").attr("href", origUrl + pad(page) + ".png");
  $("#videolink").attr("href", "https://www.youtube.com/watch?v=Y4lnZr022M8?t=" + Math.floor(page / 12));
  $("#frameLabel").text("Frame " + page);

  var sortBy = $("#sortSelect option:selected").val();
  if (sortBy === "random") {
    shuffle(submissions);
  }
  else {
    submissions.sort(function (a, b) {
      if (sortBy === "new") {
        return Date.parse(a["date"]) < Date.parse(b["date"])
      }
      else if (sortBy === "old") {
        return Date.parse(a["date"]) > Date.parse(b["date"])
      }
      else if (sortBy === "top") {
        return (a["upvotes"] - a["downvotes"]) < (b["upvotes"] - b["downvotes"]);
      }
    });
  }

  if (!submissions.length) {
    $("#frame").attr("src", origUrl + pad(page) + ".png");
  } else {
    topSub = submissions[0];
    $("#frame").attr("src", topSub["url"]);
  }
  if (prevTop && nextTop) {
    $(".prevFrame").attr("src", prevTop);
    $(".nextFrame").attr("src", nextTop);
  } else {
    $(".prevFrame").attr("src", origUrl + pad(Math.max(1, page - 1)) + ".png");
    $(".nextFrame").attr("src", origUrl + pad(Math.min(pageCount, page + 1)) + ".png");
  }

  $("#submissions").children().not(".upload").remove();

  for (var i = 0; i < submissions.length; i++) {
    $("#submissions").append(createSubmission(submissions[i]));
    updateVote(submissions[i].id, 0, 0);
  }

  $(".submission").click(function(e) {popUpComparison(this.id)});

  $("#frame").click(function () {
    if (submissions.length !== 0) {
      popUpComparison("" + topSub.id);
    }
  });

  $(".upvote").click(function (e) {
    e.stopPropagation();
      upvote($(this).parent().parent().attr("id"));
  });
  $(".downvote").click(function (e) {
    e.stopPropagation();
      downvote($(this).parent().parent().attr("id"));
  });
  $(".report").click(function (e) {
    e.stopPropagation();
      report($(this).parent().parent().attr("id"));
  });
  $(".delete").click(function (e) {
    e.stopPropagation();
      deleteSub($(this).parent().parent().attr("id"));
  });
    $(".submission").css("transform", function (i) {
        return "rotate(" + ((Math.random() - .5) * .5) + "rad) translate(" + Math.floor((Math.random() - .5) * 25) + "px," + Math.floor((Math.random() - .5) * 25) + "px)"
    });
    $(".submission").css("z-index", function (i) {
        return Math.floor(Math.random * 100 + 1000)
    });
}

function createSubmission(submission) {

  var sub = $("<div class='submission' id="+submission.id+"></div>");
  var vote = myVotes["" + submission.id];
  if(vote !== undefined) {
    if (vote.upvote === true) {
      sub.addClass("upvoted")
    }
    else {
      sub.addClass("downvoted")
    }
  }
  var votes = $("<p class='voteButtons'></p>");
  votes.append("<span class='voteButton upvote'>&#9650;</span>");
  votes.append("<span class='voteButton downvote'>&#9660;</span>");
  if(isSuper || submission.author === userid) {
    votes.append("<span class='voteButton delete'>X</span>");
  } else {
    votes.append("<span class='voteButton report'>!</span>");
  }
  sub.append(votes);
  sub.append("<br>");
  sub.append("<p class='voteButtons voteCount'</p>");
  sub.css("background-image", "url("+ submission["url"]+")");
  
  return sub;
}

function getSub(subId) {
  var submission = null;
  for (var i = 0; i < submissions.length; i++) {
    if (submissions[i].id === parseInt(subId)) {
      submission = submissions[i];
    }
  }
  return submission;
}

function updateVote(subId, delta_up, delta_down) {
  submission = getSub(subId);
  submission.upvotes += delta_up;
  submission.downvotes += delta_down;
  $("#"+subId).children(".voteCount").empty();
  $("#"+subId).children(".voteCount").html((submission.upvotes - submission.downvotes) + " (<span class='upTotal'>+" + submission.upvotes + "</span>|<span class='downTotal'>-" + submission.downvotes + "</span>)");
}

function upvote(subId) {
  console.log(subId);
  var sub = $("#"+subId);
  $.ajax({
    url: "upvote/",
    method: "POST",
    data: {"id": subId},
    success: function(data) {
      if (sub.hasClass("upvoted")) {
        sub.removeClass("upvoted");
        myVotes["" + subId] = undefined;
        updateVote(subId, -1, 0);
      }
      else {
        var down = 0;
        if (sub.hasClass("downvoted")) {
          sub.removeClass("downvoted");
          down = -1;
        }
        sub.addClass("upvoted");
        myVotes["" + subId] = {"upvote": true};
        updateVote(subId, 1, down);
      }
    },
    error: handleError,
  });
}

function downvote(subId) {
  var sub = $("#"+subId);
  $.ajax({
    url: "/ham/"+page+"/downvote/",
    method: "POST",
    data: {"id": subId},
    success: function(data) {
      if (sub.hasClass("downvoted")) {
        sub.removeClass("downvoted");
        myVotes["" + subId] = undefined;
        updateVote(subId, 0, -1);
      }
      else {
        var up = 0;
        if (sub.hasClass("upvoted")) {
          sub.removeClass("upvoted");
          up = -1;
        }
        myVotes["" + subId] = {"upvote": false};
        sub.addClass("downvoted");
        updateVote(subId, up, 1);
      }
    },
    error: handleError
  });
}

function deleteSub(subId) {
  $.ajax({
    url: "/ham/" + page + "/delete/",
    method: "POST",
    data: {"id": subId},
    success: function (data) {
      window.location.reload()
    },
    error: handleError
  });
}

function report(subId) {
  $.ajax({
    url: "/ham/" + page + "/report/",
    method: "POST",
    data: {"id": subId},
    success: function (data) {
      window.alert("submission reported successfully");
    },
    error: handleError,
  });
}

function isMobile() {
  return ("ontouchstart" in document.documentElement);
}

function playMusic() {  
  //$("#music").get(0).getElementById("player").play();
}

function clean(node) {
  for(var n = 0; n < node.childNodes.length; n ++) {
    var child = node.childNodes[n];
    if(child.nodeType === 8 || (child.nodeType === 3 && !/\S/.test(child.nodeValue))){
      node.removeChild(child);
      n--;
    } else if(child.nodeType === 1){
      clean(child);
    }
  }
}

function getPageName() {
  path = window.location.pathname
  if(/\/ham\/\d+\/?/g.exec(path) !== null) {
    return "ham";
  } else if (/\/statistics\/?/g.exec(window.location.pathname) !== null) {
    return "stat";
  } else if (/\/me\/?/g.exec(window.location.pathname) !== null) {
    return "me";
  } else if (/\/statistics\/?/g.exec(window.location.pathname) !== null) {
    return "login";
  } else {
    return "index";
  }
}

function pad(num) {
  var s = "000" + num;
  return s.substr(s.length - 4);
}


// Modal comparison
function popUpComparison(subId) {
  if(getSub(subId) == null) {
    return;
  }
  $('#comparisonBg').css('background-image', 'url(' + origUrl + pad(page) + ".png)");
  $('#modalComparison').attr("src", getSub(subId)["url"]);
  $("#comparisonModal").css({"display": "block"});
}

// Evil function
// Randomly insert a modal popup 10% of the time you lose focus of the window
function newsletter() {
  // let modal = document.getElementById('newsletter');
  // if (Math.random() < 0.1) {
  //   modal.style.display = "block";
  // }
}

function isEmpty(str) {
  return (str === undefined || str === null || str === "");

}

function handleError(xhr, status, error) {
  if (xhr.status === 400) {
    window.alert(isEmpty(xhr.responseText) ? "bad request" : xhr.responseText);
  }
  else if(xhr.status === 401) {
    var r = window.confirm("You must log in to do that.\nWould you like to log in?");
    if(r) {
      window.localStorage.setItem("redirect", window.location.href);
      loadPage(htmlUrl + "Signup.html", "/signup/")
    }
  } else if (xhr.status === 429) {
    window.alert("The server says you're doing too much, please cool it and come back later.");
  } else if (xhr.status === 500) {
    window.alert("Really bad request (server error)");
  }
}


function shuffle(a) {
  var j, x, i;
  for (i = a.length - 1; i > 0; i--) {
    j = Math.floor(Math.random() * (i + 1));
    x = a[i];
    a[i] = a[j];
    a[j] = x;
  }
}


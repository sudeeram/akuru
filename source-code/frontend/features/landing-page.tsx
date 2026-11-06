'use client';

import Image from 'next/image';
import { Link } from '@tanstack/react-router';

import {
  ArrowRight,
  BookOpen,
  Check,
  ChevronRight,
  Layers3,
  MessageCircle,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Users,
} from 'lucide-react';

const features = [
  {
    icon: MessageCircle,
    label: 'UNDERSTAND',
    title: 'A little help. A bigger understanding.',
    text: 'Ask your AI tutor a question, work through an explanation and explore ideas with references to your learning materials.',
    color: 'purple',
  },
  {
    icon: Layers3,
    label: 'REMEMBER',
    title: 'Make knowledge stick.',
    text: 'Practise with reviewed flashcards. Choose a difficulty, rate your understanding and see your own mastery grow across a topic.',
    color: 'orange',
  },
  {
    icon: BookOpen,
    label: 'EXPLORE',
    title: 'Your bookshelf, wherever you learn.',
    text: 'Read published textbook topics, revisit explanations and open the original visual-reference pages, including a flipbook view.',
    color: 'green',
  },
  {
    icon: TrendingUp,
    label: 'PREPARE',
    title: 'Turn practice into your next step.',
    text: 'Bring together practice, assessment feedback, progress and study planning to focus your revision on the areas that need attention.',
    color: 'blue',
  },
];

export function LandingPage() {
  return (
    <div className="akuru-landing">
      <a className="al-skip" href="#landing-content">
        Skip to content
      </a>
      <header className="al-header">
        <Link to="/" className="al-logo" aria-label="AKURU home">
          <Image
            unoptimized
            src="/akuru-bots/akuru-bot-wink.png"
            alt=""
            width="52"
            height="52"
          />
          <span>
            AKURU<span className="al-logo-dot">.</span>
          </span>
        </Link>
        <nav aria-label="Main navigation">
          <a href="#features">Why AKURU</a>
          <a href="#how-it-works">How it works</a>
          <a href="#families">For families</a>
        </nav>
        <Link className="al-button al-button-small" to="/login">
          Log in <ArrowRight size={16} />
        </Link>
      </header>
      <main id="landing-content">
        <section className="al-hero al-container">
          <div className="al-hero-copy">
            <span className="al-kicker">
              <span /> BIG CURIOSITY. LITTLE STEPS.
            </span>
            <h1>
              That “I get it!”
              <br />
              feeling.
              <br />
              <em>More often.</em>
            </h1>
            <p>
              A learning companion for the questions, the practice and the small
              breakthroughs. AKURU helps students build understanding—and the
              confidence to keep going.
            </p>
            <div className="al-hero-actions">
              <Link className="al-button" to="/login">
                Enter your learning space <ArrowRight size={18} />
              </Link>
              <a className="al-text-link" href="#features">
                Meet AKURU <ChevronRight size={17} />
              </a>
            </div>
            <div className="al-hero-note">
              <ShieldCheck size={17} /> Personal learning. Connected families.
            </div>
          </div>
          <div
            className="al-hero-art"
            aria-label="AKURU BOT surrounded by examples of learning tools"
          >
            <div className="al-orbit al-orbit-one" />
            <div className="al-orbit al-orbit-two" />
            <span className="al-art-star al-star-one">✦</span>
            <span className="al-art-star al-star-two">✦</span>
            <div className="al-art-label">
              <Sparkles size={15} /> YOUR CURIOSITY BELONGS HERE
            </div>
            <Image
              unoptimized
              className="al-hero-bot"
              src="/akuru-bots/akuru-bot-reader.png"
              alt="AKURU BOT enjoying a book"
              width="390"
              height="430"
              fetchPriority="high"
            />
            <div className="al-float al-float-question">
              <span className="al-float-icon">
                <MessageCircle size={21} />
              </span>
              <div>
                <strong>Why does that happen?</strong>
                <small>Let’s work it out together.</small>
              </div>
            </div>
            <div className="al-float al-float-progress">
              <span className="al-progress-ring">
                <Check size={20} />
              </span>
              <div>
                <strong>A little clearer.</strong>
                <small>A little more confident.</small>
              </div>
            </div>
            <span className="al-art-caption">
              Your next discovery starts with a question.
            </span>
          </div>
        </section>
        <div className="al-subject-strip">
          <div className="al-container">
            <span>MADE FOR CURIOUS MINDS</span>
            <strong>Understand it.</strong>
            <span className="al-strip-dot">✦</span>
            <strong>Practise it.</strong>
            <span className="al-strip-dot">✦</span>
            <strong>Make it yours.</strong>
          </div>
        </div>
        <section className="al-container al-section" id="features">
          <div className="al-section-heading">
            <span className="al-kicker">
              A TOOLKIT FOR YOUR NEXT BREAKTHROUGH
            </span>
            <h2>
              Less “where do I start?”
              <br />
              More <em>“let’s try.”</em>
            </h2>
            <p>
              From a tricky concept to a revision session, keep the pieces of
              learning in one welcoming space.
            </p>
          </div>
          <div className="al-feature-grid">
            {features.map(({ icon: Icon, label, title, text, color }) => (
              <article className={`al-feature al-${color}`} key={label}>
                <span className="al-feature-icon">
                  <Icon size={25} />
                </span>
                <span className="al-card-label">{label}</span>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </section>
        <section className="al-learning-section" id="how-it-works">
          <div className="al-container al-learning-grid">
            <div className="al-demo">
              <div className="al-demo-top">
                <span className="al-demo-dots">● ● ●</span>
                <span>A LITTLE LOOK INSIDE</span>
              </div>
              <div className="al-demo-body">
                <span className="al-demo-subject">
                  BIOLOGY · LEARNING TOGETHER
                </span>
                <div className="al-demo-question">
                  What makes a living thing… living?
                </div>
                <div className="al-demo-reply">
                  <Image
                    unoptimized
                    src="/akuru-bots/akuru-bot-idea.png"
                    alt=""
                    width="65"
                    height="75"
                    loading="lazy"
                  />
                  <p>
                    Let’s start with what living things do. Can you think of
                    something a plant and an animal both need?
                  </p>
                </div>
                <div className="al-demo-tools">
                  <span>
                    <BookOpen size={15} /> Textbook references
                  </span>
                  <span>
                    <Layers3 size={15} /> Keep practising
                  </span>
                </div>
                <p className="al-demo-caption">
                  Illustrative learning conversation
                </p>
              </div>
            </div>
            <div className="al-learning-copy">
              <span className="al-kicker">
                LEARNING WITH A LITTLE DIRECTION
              </span>
              <h2>
                Ask. Explore.
                <br />
                Practise. <em>Progress.</em>
              </h2>
              <p>
                AKURU connects the learning material with what comes next, so a
                question can become a useful study session.
              </p>
              <ol className="al-steps">
                <li>
                  <span>01</span>
                  <div>
                    <h3>Start with your subject</h3>
                    <p>
                      Open the topics and resources made available for your
                      course, grade and term.
                    </p>
                  </div>
                </li>
                <li>
                  <span>02</span>
                  <div>
                    <h3>Find your way into the topic</h3>
                    <p>
                      Read, ask your tutor or work through a set of flashcards
                      at your own pace.
                    </p>
                  </div>
                </li>
                <li>
                  <span>03</span>
                  <div>
                    <h3>Know what to work on next</h3>
                    <p>
                      Use feedback and your personal progress to guide your next
                      practice session.
                    </p>
                  </div>
                </li>
              </ol>
            </div>
          </div>
        </section>
        <section className="al-container al-section" id="families">
          <div className="al-section-heading">
            <span className="al-kicker">
              INDEPENDENT LEARNERS. CONNECTED SUPPORT.
            </span>
            <h2>
              Their own journey.
              <br />
              <em>A shared commitment.</em>
            </h2>
          </div>
          <div className="al-role-grid">
            <article>
              <span className="al-role-number">01 / STUDENTS</span>
              <h3>A space that’s yours.</h3>
              <p>
                Your tutors, your resources, your practice and your progress.
                Each student has a separate learning profile.
              </p>
              <span className="al-role-footer">
                <Sparkles size={18} /> Build confidence, one topic at a time.
              </span>
            </article>
            <article>
              <span className="al-role-number">02 / PARENTS</span>
              <h3>Stay close to the learning.</h3>
              <p>
                Follow each child’s progress, review feedback and see
                tutor-session summaries from your family portal.
              </p>
              <span className="al-role-footer">
                <Users size={18} /> Support each child individually.
              </span>
            </article>
            <article>
              <span className="al-role-number">03 / ADMINISTRATORS</span>
              <h3>Give learning a strong foundation.</h3>
              <p>
                Manage accounts and curriculum coverage, review textbook content
                and exam evidence, and control which resources are released.
              </p>
              <span className="al-role-footer">
                <ShieldCheck size={18} /> Review first. Release with care.
              </span>
            </article>
          </div>
        </section>
        <section className="al-container al-exam-note">
          <BookOpen size={29} />
          <div>
            <h3>Built around the learning that matters.</h3>
            <p>
              AKURU’s current focus is Pearson Edexcel International GCSE study,
              including textbook-based learning, reviewed flashcards and
              exam-paper preparation. Access to tutors, papers and other
              resources depends on enrolment, content approval and release
              settings.
            </p>
          </div>
        </section>
        <section className="al-container al-cta">
          <div>
            <span className="al-kicker">A LITTLE PROGRESS, EVERY DAY</span>
            <h2>
              Bring your curiosity.
              <br />
              We’ll bring <em>AKURU.</em>
            </h2>
            <p>Already have an account? Your learning space is waiting.</p>
            <Link to="/login" className="al-button">
              Let’s get learning <ArrowRight size={18} />
            </Link>
            <small>
              Accounts are currently provided by an AKURU administrator.
            </small>
          </div>
          <Image
            unoptimized
            src="/akuru-bots/akuru-bot-wink.png"
            alt="AKURU BOT waving hello"
            width="260"
            height="290"
            loading="lazy"
          />
        </section>
      </main>
      <footer className="al-container al-footer">
        <Link to="/" className="al-logo">
          <Image
            unoptimized
            src="/akuru-bots/akuru-bot-wink.png"
            alt=""
            width="44"
            height="44"
          />
          <span>
            AKURU<span className="al-logo-dot">.</span>
          </span>
        </Link>
        <p>Small steps. Lasting understanding.</p>
        <Link to="/login">
          Log in <ArrowRight size={15} />
        </Link>
        <small>
          AKURU is an independent learning platform, not affiliated with or
          endorsed by Pearson.
        </small>
      </footer>
    </div>
  );
}
